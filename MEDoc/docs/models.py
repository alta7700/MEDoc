from django.db import models
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey
from bots.vk_bot.vk_connection import user_session, gr_session, VK_STR_GROUP_ID


class Subject(models.Model):
    title: str = models.CharField(verbose_name='Название', max_length=100)
    short_title: str = models.CharField(verbose_name='Краткое название', max_length=20, unique=True)

    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
        ordering = ['short_title']

    def __str__(self):
        return self.short_title


class DocFolderType(models.Model):
    title: str = models.CharField(verbose_name='Для документа', max_length=40, blank=True)
    title_plural: str = models.CharField(verbose_name='Для папки', max_length=40, blank=True)

    class Meta:
        verbose_name = 'Тип документа'
        verbose_name_plural = 'Тип папки'
        ordering = ['title']

    def __str__(self):
        return self.title_plural


class Doc(MPTTModel):
    title: str = models.CharField(verbose_name='Название', max_length=200)
    ext: str = models.CharField(verbose_name='Расширение файла', max_length=15, blank=True)
    is_folder: bool = models.BooleanField(verbose_name='Это папка?')
    parent = TreeForeignKey(verbose_name='Родитель', to='self', related_name='children', on_delete=models.PROTECT,
                            null=True, limit_choices_to={'is_folder': True})
    subject: Subject = models.ForeignKey(verbose_name='Предмет', to=Subject, on_delete=models.PROTECT,
                                         null=True, blank=True, related_name='documents', default=None)
    type: DocFolderType = models.ForeignKey(verbose_name='Тип', to=DocFolderType, on_delete=models.PROTECT,
                                            null=True, blank=True, related_name='documents', default=None)
    vk_doc_id: int = models.PositiveBigIntegerField(verbose_name='ID документа ВК', null=True, blank=True, default=None)
    owner = models.ForeignKey(verbose_name='Владелец', to=settings.AUTH_USER_MODEL, on_delete=models.SET_DEFAULT,
                              default=1, null=True, blank=True)
    original = models.ForeignKey(verbose_name='Оригинал', to='self', on_delete=models.SET_NULL, related_name='copies',
                                 null=True, blank=True, limit_choices_to={'is_folder': False})

    class MPTTMeta:
        order_insertion_by = ['title']

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        indexes = [
            models.Index(fields=['is_folder', ]),
            models.Index(fields=['subject', 'type']),
            models.Index(fields=['parent', ]),
            models.Index(fields=['id', ])
        ]

    def __str__(self):
        return self.title

    def get_ancestors_names(self):
        if self.is_folder:
            if self.parent:
                parents = list(self.get_ancestors(include_self=True))
                return ' - '.join(p.title for p in parents)
            else:
                return self.title
        else:
            return self.title

    def is_copy(self):
        return True if self.original else False

    def get_short_download_url(self):
        if not self.is_folder:
            return f'https://vk.com/doc{VK_STR_GROUP_ID}_{self.vk_doc_id}'

    def get_vk_doc_title(self):
        self.subject: Subject
        title = self.subject.short_title + " " if self.subject else ""
        title += self.type.title + " " if self.type else ""
        title += self.title
        return title

    def change_doc_vk_title(self):
        success = user_session.method('docs.edit', {
            'owner_id': VK_STR_GROUP_ID,
            'doc_id': self.vk_doc_id,
            'title': self.get_vk_doc_title()
        }) == 1
        if success:
            self.copies.update(title=self.title)
        return success

    def delete_doc_from_vk(self):
        return user_session.method('docs.delete', {
            'owner_id': VK_STR_GROUP_ID,
            'doc_id': self.vk_doc_id
        })


class Offer(models.Model):
    user = models.ForeignKey(verbose_name='Кто предложил', to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, related_name='offers_add')
    title: str = models.CharField(verbose_name='Название', max_length=200)
    folder: Doc = TreeForeignKey(verbose_name='Папка', to=Doc, on_delete=models.SET_NULL, null=True,
                                 related_name='offers')
    subject: Subject = models.ForeignKey(verbose_name='Предмет', to=Subject, on_delete=models.PROTECT, null=True, blank=True)
    type: DocFolderType = models.ForeignKey(verbose_name='Тип', to=DocFolderType, on_delete=models.PROTECT,
                                            null=True, blank=True)
    comment: str = models.TextField(verbose_name='Комментарий', blank=True)
    conv_mes_id: int = models.PositiveBigIntegerField(verbose_name='ID Сообщение', null=True)
    index_in_message: int = models.PositiveSmallIntegerField(verbose_name='Номер документа в сообщении')
    upload_dt = models.DateTimeField(verbose_name='Время создания', auto_now_add=True)
    doc_created: Doc = models.ForeignKey(verbose_name='Созданный документ', to=Doc, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='offered_from')

    class Meta:
        verbose_name = 'Предложение'
        verbose_name_plural = 'Предложения'
        indexes = [
            models.Index(fields=['subject', 'type'])
        ]
        ordering = ['subject', 'type']

    def __str__(self):
        return self.title

    def doc_created_bool(self):
        return 'Да' if self.doc_created else 'Нет'
    doc_created_bool.short_description = 'Обработан'

    def get_folder_ancestors_names(self):
        return self.folder.get_ancestors_names() if self.folder else 'Папка удалена'

    def get_vk_download_url(self):
        message = gr_session.method('messages.getByConversationMessageId', {
            'peer_id': self.user.id_vk,
            'conversation_message_ids': self.conv_mes_id
        })
        if message:
            if message.get('count') == 1:
                attachments = message['items'][0].get('attachments')
                if attachments:
                    try:
                        attach = attachments[self.index_in_message]
                        if attach['type'] == 'doc':
                            return attach['doc']['url']
                    except IndexError:
                        pass
        return ''
