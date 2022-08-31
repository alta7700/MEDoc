from django.db import models
from django.conf import settings


class VkTempValue(models.Model):
    vk_id = models.PositiveBigIntegerField(verbose_name='ВК ID', unique=True)
    user = models.ForeignKey(verbose_name='Пользователь', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             null=True, related_name='caches')
    last_q_time = models.DateTimeField(verbose_name='Время запроса', auto_now=True)
    code = models.CharField(verbose_name='reg_code', max_length=8)
    current_folder = models.ForeignKey('docs.Doc', on_delete=models.SET_NULL, default=None,
                                       related_name='now_ids', null=True)
    favourites = models.ManyToManyField(to='docs.Doc', verbose_name='Редакт. избранного')
    captcha = models.CharField(verbose_name='Ввод капчи', max_length=20, default='')
