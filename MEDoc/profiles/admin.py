from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from .models import User, Faculty
from docs.models import Doc


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'short_title')
    list_display_links = list_display


@admin.register(User)
class MyUserAdmin(UserAdmin):
    list_display = ('id', 'faculty', 'course', 'first_name', 'last_name', 'username', 'id_vk')
    search_fields = ('last_name', 'first_name', 'username')
    list_filter = ('faculty', 'course', 'is_staff')
    readonly_fields = ['date_joined', 'last_login']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'id_vk', 'faculty', 'course')}),
        (None, {'fields': ('favourites', 'top_folder', 'avatar')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    def get_queryset(self, request):
        user = request.user
        if user.is_active and user.is_superuser:
            return User.objects.order_by('last_login')
        else:
            return User.objects.filter(faculty=user.faculty, course=user.course)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'top_folder':
            kwargs['queryset'] = Doc.objects.filter(is_folder=True)
        return super(MyUserAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'favourites':
            kwargs['queryset'] = Doc.objects.filter(is_folder=False)
        return super(MyUserAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_view_permission(self, request, obj=None):
        return True

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not request.user.is_superuser:
            return redirect(f'https://vk.com/id{User.objects.get(id=object_id).id_vk}')
        return super(MyUserAdmin, self).change_view(request, object_id, form_url, extra_context)
