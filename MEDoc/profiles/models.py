from django.db import models
from django.contrib.auth.models import AbstractUser
from mptt.models import TreeForeignKey
from docs.models import Doc


class Faculty(models.Model):
    title = models.CharField(verbose_name='Название', max_length=30, unique=True)
    short_title = models.CharField(verbose_name='Краткое название', max_length=7, unique=True)
    years: int = models.PositiveSmallIntegerField(verbose_name='Длительность обучения (лет)')

    class Meta:
        verbose_name = 'Факультет'
        verbose_name_plural = 'Факультеты'
        ordering = ['id']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super(Faculty, self).save(*args, **kwargs)
        if kwargs.get('force_insert') or not kwargs.get('force_update'):
            self.refresh_from_db()
            faculty_folder = Doc(
                title=self.short_title,
                ext=str(self.id),
                is_folder=True,
                parent=None
            )
            faculty_folder.save()
            for year in range(1, self.years + 1):
                Doc(
                    title=f'{year} Курс',
                    ext=f'{self.id}.{year}',
                    is_folder=True,
                    parent=faculty_folder
                ).save()


def user_avatar_path(instance, filename):
    return f'user_avatars/{instance.id}.jpeg'


class User(AbstractUser):
    MAN = True
    WOMAN = False
    NO_SEX = None
    SEX_CHOICE = ((NO_SEX, 'Не указан'), (MAN, 'Мужской'), (WOMAN, 'Женский'))

    sex = models.BooleanField(verbose_name='Пол', choices=SEX_CHOICE, null=True)
    faculty = models.ForeignKey(verbose_name='Факультет', to=Faculty, on_delete=models.PROTECT,
                                null=True, blank=True)
    course = models.PositiveSmallIntegerField(verbose_name='Курс', blank=True, null=True)
    id_vk = models.PositiveBigIntegerField(verbose_name='ВК id', null=True, blank=True, unique=True)
    favourites = models.ManyToManyField(verbose_name='Избранное', to='docs.Doc', blank=True)
    top_folder = TreeForeignKey(verbose_name='Доступ', to='docs.Doc', on_delete=models.CASCADE,
                                null=True, blank=True, related_name='admins')
    avatar = models.ImageField(verbose_name='Аватар', upload_to=user_avatar_path, null=True, blank=True)
    last_folder_in_bot = models.ForeignKey(verbose_name='Находится в папке', to='docs.Doc', on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name='bot_users')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['faculty', 'course']),
            models.Index(fields=['id_vk', ])
        ]

    def __str__(self):
        full_name = self.get_full_name()
        return full_name if full_name else self.username
