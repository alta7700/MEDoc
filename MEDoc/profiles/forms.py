import requests
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe
from django import forms
from bots.models import VkTempValue
from bots.vk_bot.bot_funcs import show_start_folders, user_session
from .models import User, Faculty
from datetime import datetime, timedelta


class MyUserChangeForm(UserChangeForm):
    pass


class BotUserCreationForm(UserCreationForm):
    username = forms.CharField(label='Логин', max_length=150, widget=forms.TextInput(attrs={'class': 'form-input'}))
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    faculty = forms.ModelChoiceField(label='Факультет', queryset=Faculty.objects.all(), required=False,
                                     empty_label='Не указан', widget=forms.Select(attrs={'class': 'form-input'}))
    course = forms.IntegerField(label='Курс', min_value=1, max_value=6, required=False,
                                widget=forms.NumberInput(attrs={'class': 'form-input'}))
    reg_code = forms.CharField(label=mark_safe("Временный код\n(Спроси у <a href='https://vk.com/im?sel=-210457778'>бо"
                                               "та</a>)"),
                               required=True, min_length=8, max_length=8,
                               widget=forms.TextInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'faculty', 'course', 'reg_code')

    def clean(self):
        cleaned_data = super(BotUserCreationForm, self).clean()
        faculty, course = cleaned_data['faculty'], cleaned_data['course']
        if faculty:
            if course:
                if course > faculty.years:
                    self.add_error('course',
                                   forms.ValidationError(message='В выбранном факультете нет столько курсов',
                                                         code='invalid'))
        access_code = cleaned_data['reg_code']
        try:
            vk_temp = VkTempValue.objects.get(code=access_code)
            if vk_temp.last_q_time < datetime.now() - timedelta(minutes=3):
                self.add_error('reg_code',
                               forms.ValidationError(message='Код устарел (действует 3 минуты)', code='invalid'))
        except VkTempValue.DoesNotExist:
            self.add_error('reg_code', forms.ValidationError(message='Код недействителен', code='invalid'))
        return cleaned_data

    def save(self, commit=True):
        user = super(BotUserCreationForm, self).save(commit=False)
        cleaned_data = self.cleaned_data
        vk_temp = VkTempValue.objects.get(code=cleaned_data['reg_code'])
        user.id_vk = vk_temp.vk_id
        vk_temp.code = ''
        vk_temp.save()
        avatar = None
        try:
            user_info = user_session.method('users.get', {
                'user_ids': str(vk_temp.vk_id),
                'fields': 'sex,has_photo,photo_100'
            })
            if user_info:
                user_info = user_info[0]
                user.first_name = user_info.get('first_name', '')
                user.last_name = user_info.get('last_name', '')
                sex = user_info.get('sex', None)
                if sex:
                    if sex == 1:
                        user.sex = User.WOMAN
                    elif sex == 2:
                        user.sex = User.MAN

                if user_info.get('has_photo') == 1:
                    response = requests.get(user_info.get('photo_100'))
                    if response.status_code == 200 and response.headers['Content-Type'] == 'image/jpeg':
                        img = NamedTemporaryFile()
                        img.write(response.content)
                        avatar = File(img)
            else:
                user.first_name = ''
                user.last_name = ''
        except:
            user.first_name = ''
            user.last_name = ''
        if commit:
            user.save()
            if avatar:
                user.avatar = avatar
                user.save(update_fields=('avatar', ))
            g = Group.objects.get(name='bot_user')
            user.groups.add(g)
            vk_temp.user = user
            vk_temp.save()
            show_start_folders(vk_temp)
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
