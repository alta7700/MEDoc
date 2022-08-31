from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from .forms import BotUserCreationForm, UserLoginForm


def index(request):
    return render(request, 'profiles/index.html', {'title': 'Главная'})


def profile(request):
    return render(request, 'profiles/profile.html', {'title': 'Профиль'})


def about(request):
    return render(request, 'profiles/about-us.html', {'title': 'О нас'})


class RegisterView(CreateView):
    form_class = BotUserCreationForm
    template_name = 'profiles/registration.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect('/profile/')
        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), **{'title': 'Регистрация'}}


class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'profiles/login.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), **{'title': 'Авторизация'}}

    def get_success_url(self):
        return reverse_lazy('home')


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/login/')
