from abc import ABC
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from profiles.models import Faculty


def fill_groups():
    groups = [
        {
            'name': 'Админ курса',
            'perms': [
                'add_doc',
                'change_doc',
                'delete_doc',
                'view_doc',
                'view_offer'
                'view_subject',
                'view_doc_folder_type'
            ]
        },
        {
            'name': 'bot_user',
            'perms': [
                'add_offer',
                'view_doc',
            ]
        }
    ]
    for gr in groups:
        g, created = Group.objects.get_or_create(name=gr['name'])
        if created:
            permissions = Permission.objects.filter(codename__in=gr['perms'])
            g.permissions.set(permissions)
            g.save()


def fill_faculties():
    faculties = [
        (1, 'Лечебный', 'ЛЕЧ', 6),
        (2, 'Медико-профилактический', 'МПФ', 6),
        (3, 'Педиатрический', 'ПЕД', 6),
        (4, 'Стоматологический', 'СТОМ', 5),
        (5, 'Фармакологический', 'ФАРМ', 5)
    ]

    for f in faculties:
        if not Faculty.objects.filter(title=f[1]):
            faculty = Faculty(title=f[1], short_title=f[2], years=f[3])
            faculty.save()


class Command(BaseCommand, ABC):
    help = 'Загрузка предопределенных'

    def handle(self, *args, **options):
        fill_groups()
        fill_faculties()

