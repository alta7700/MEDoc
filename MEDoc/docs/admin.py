from .forms import *
from .models import Doc, Offer, Subject, DocFolderType
from .tasks import download_doc_and_upload_vk
from django.contrib import admin
from django.shortcuts import redirect
from django_mptt_admin.admin import DjangoMpttAdmin
from django.core.exceptions import ValidationError


@admin.register(Doc)
class DocAdmin(DjangoMpttAdmin):
    list_display = ('title', 'subject', 'type', 'parent', 'is_folder')
    search_fields = ('title', '=subject__short_title', '=type__title')
    change_tree_template = 'docs/admin_doc_change_list.html'
    change_list_template = 'docs/admin_doc_grid_view.html'
    change_form_template = 'docs/admin_doc_change_view.html'
    add_form_template = 'docs/admin_doc_change_view.html'

    def get_list_filter(self, request):
        if request.build_absolute_uri('?').endswith('/grid/'):
            return ['subject', 'type', 'is_folder']
        return []

    @staticmethod
    def get_list_view_custom_objects_tools_items(request):
        if request.GET.get('all'):
            url = request.build_absolute_uri('?')
            title = 'Показать МОИ'
        else:
            url = request.build_absolute_uri('?') + '?all=1'
            title = 'Показать ВСЁ'
        return [{'title': title, 'url': url}]

    def grid_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['custom_object_tools_items'] = self.get_list_view_custom_objects_tools_items(request)
        return super(DocAdmin, self).grid_view(request, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['custom_object_tools_items'] = self.get_list_view_custom_objects_tools_items(request)
        return super(DocAdmin, self).changelist_view(request, extra_context=extra_context)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        items = []
        if change:
            if obj.is_folder:
                context['title'] = 'Изменить Папку'
            else:
                items.append({'title': 'Посмотреть документ', 'url': obj.get_short_download_url()})
                if not obj.is_copy():
                    context['custom_buttons'] = [{'title': 'Скопировать', 'action': '_copy_to_other_folder'}]
        else:
            if 'insert_at' in request.GET:
                url = request.build_absolute_uri('?') + f'?insert_at={request.GET.get("insert_at")}'
                if 'insert_doc' in request.GET:
                    items.append({'title': 'Добавить папку', 'url': url})
                else:
                    context['title'] = 'Добавить Папку'
                    items.append({'title': 'Добавить документ', 'url': url + '&insert_doc=1'})
        context['custom_object_tools_items'] = items
        return super(DocAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if '_copy_to_other_folder' in request.POST:
            return redirect(f'/admin/docs/doc/add/?copy_doc={object_id}')
        return super(DocAdmin, self).changeform_view(request, object_id, form_url, extra_context)

    def response_post_save_add(self, request, obj):
        if 'offer' in request.GET:
            return redirect('/admin/docs/offer/')
        return super(DocAdmin, self).response_post_save_add(request, obj)

    def get_form(self, request, obj=None, change=False, **kwargs):
        if not change:
            if 'offer' in request.GET:
                form = DocAddByOfferForm
            elif 'copy_doc' in request.GET:
                form = AddCopyDocForm
            elif 'insert_at' in request.GET:
                if 'insert_doc' in request.GET:
                    form = InsertDocAtFolderForm
                else:
                    form = InsertFolderAtFolderForm
        else:
            if obj.is_folder:
                form = EditFolderForm
            else:
                if obj.is_copy():
                    form = EditCopyDocForm
                else:
                    form = EditOriginalDocForm

        user = request.user
        if user.top_folder:
            parent_queryset = user.top_folder.get_descendants(include_self=True).filter(is_folder=True)
        else:
            parent_queryset = Doc.objects.filter(is_folder=True)

        class ReturnForm(form):
            def __init__(self, *args, **kwargs_):
                super(DocAdminForm, self).__init__(*args, **kwargs_)
                self.fields['parent'].queryset = parent_queryset

        return ReturnForm

    def get_changeform_initial_data(self, request):
        initial_data = super(DocAdmin, self).get_changeform_initial_data(request)
        values = {}
        if 'offer' in request.GET:
            offer = Offer.objects.get(id=request.GET.get('offer'))
            split_title = offer.title.split('.')
            doc_ext = split_title[-1] if len(split_title) > 1 else ''
            values = {
                'title': offer.title,
                'ext': doc_ext,
                'parent': offer.folder.id if offer.folder else None,
                'offer': offer.id
            }
        elif 'copy_doc' in request.GET:
            copy_doc = Doc.objects.get(id=request.GET.get('copy_doc'))
            values = {'original': copy_doc}
        return {**initial_data, **values}

    def get_fieldsets(self, request, obj=None):
        if not obj:
            if 'offer' in request.GET:
                return (
                    ('Доступные поля', {
                        'fields': ('title', 'ext', 'parent')
                    }),
                    (None, {
                        'classes': ('empty-form', ),
                        'fields': ('offer', ),
                    }),
                )
            elif 'copy_doc' in request.GET:
                return (
                    ('Доступные поля', {'fields': ('parent', )}),
                    (None, {'classes': ('empty-form', ), 'fields': ('original', )})
                )
            elif 'insert_at' in request.GET:
                if 'insert_doc' in request.GET:
                    return (
                        (None, {'fields': ('title', 'ext', 'doc_file', )}),
                        (None, {'fields': ('parent', ), 'classes': ('empty-form', )})
                    )
                else:
                    fields = ['title']
                    parent = Doc.objects.get(id=request.GET.get('insert_at'))
                    if not parent.subject:
                        fields.append('subject')
                    if not parent.type:
                        fields.append('type')
                    return (
                        (None, {'fields': fields}),
                        (None, {'fields': ('parent', ), 'classes': ('empty-form', )})
                    )
        else:
            if obj.is_folder:
                return (
                    (None, {'fields': ('title', 'parent')}),
                    (None, {'fields': ('subject', 'type', 'owner')})
                )
            else:
                if obj.is_copy():
                    return [(None, {'fields': ('original', 'parent', 'subject', 'type', 'owner')}), ]
                else:
                    return (
                        (None, {'fields': ('title', 'ext')}),
                        (None, {'fields': ('parent', 'subject', 'type', 'owner')})
                    )

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            if 'offer' in request.GET:
                return []
            elif 'copy_doc' in request.GET:
                return []
            elif 'insert_at' in request.GET:
                if 'insert_doc' in request.GET:
                    return []
                else:
                    parent = Doc.objects.select_related('subject', 'type').get(id=request.GET.get('insert_at'))
                    fields = []
                    if parent.subject:
                        fields.append('subject')
                    if parent.type:
                        fields.append('type')
                    return fields
        else:
            if obj.is_folder:
                return ['subject', 'type', 'owner']
            else:
                if obj.is_copy():
                    return ['original', 'subject', 'type', 'owner']
                else:
                    return ['subject', 'type', 'owner']

    def is_drag_and_drop_enabled(self) -> bool:
        return False

    def filter_tree_queryset(self, queryset, request):
        return self.get_queryset(request)

    def get_object(self, request, object_id, from_field=None):
        try:
            return Doc.objects.get(id=object_id)
        except (Doc.DoesNotExist, ValidationError, ValueError):
            return None

    def get_queryset(self, request):
        user = request.user
        print(request)
        if not request.GET.get('all'):
            if user.top_folder:
                return user.top_folder.get_descendants(include_self=True)
        return Doc.objects.all()

    def has_add_permission(self, request):
        if super(DocAdmin, self).has_add_permission(request):
            if request.GET.get('offer'):
                offer = Offer.objects.get(id=request.GET['offer'])
                if not offer.doc_created:
                    return True
            elif request.GET.get('copy_doc'):
                doc = Doc.objects.get(id=request.GET['copy_doc'])
                if not (doc.is_folder or doc.is_copy()):
                    return True
            elif request.GET.get('insert_at'):
                folder = Doc.objects.get(id=request.GET['insert_at'])
                if folder.is_folder:
                    top_folder = request.user.top_folder
                    if top_folder:
                        if folder in top_folder.get_descendants(include_self=True):
                            return True
                    else:
                        return True
        return False

    def has_change_permission(self, request, obj=None):
        if super(DocAdmin, self).has_change_permission(request, obj):
            user = request.user
            if obj:
                if obj.is_copy():
                    return False
                elif '_copy_to_other_folder' in request.POST:
                    return True
                else:
                    if (obj.owner == user) or user.is_superuser:
                        return True
                    top_folder = request.user.top_folder
                    if top_folder:
                        return obj.is_descendant_of(top_folder)
                    return False
            else:
                return True
        else:
            return False

    def has_delete_permission(self, request, obj=None):
        if super(DocAdmin, self).has_delete_permission(request, obj):
            user = request.user
            if obj:
                return (obj.owner == user) or user.is_superuser
            else:
                return False
        else:
            return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
            if 'offer' in request.GET:
                offer_id = request.GET.get('offer')
                obj_values = {
                    'title': obj.title,
                    'ext': obj.ext,
                    'parent': obj.parent.id,
                    'owner': obj.owner.id,
                    'offer': offer_id
                }
                download_doc_and_upload_vk.delay(**obj_values)
            elif 'copy_doc' in request.GET:
                copy_obj = Doc.objects.get(id=request.GET.get('copy_doc'))
                copy_obj.pk = None
                copy_obj.original = form.cleaned_data['original']
                copy_obj.parent = form.cleaned_data['parent']
                copy_obj.owner = request.user
                copy_obj.save()
            elif 'insert_at' in request.GET:
                if 'insert_doc' in request.GET:
                    parent = obj.parent
                    obj.subject, obj.type = parent.subject, parent.type
                    doc_title = obj.get_vk_doc_title()
                    with open(doc_title, 'wb') as f:
                        f.write(form.cleaned_data['doc_file'].read())
                    obj_values = {
                        'title': obj.title,
                        'ext': obj.ext,
                        'parent': obj.parent.id,
                        'owner': obj.owner.id,
                        'file': True
                    }
                    download_doc_and_upload_vk.delay(**obj_values)
                else:
                    obj.is_folder = True
                    parent = obj.parent
                    if parent.subject:
                        obj.subject = parent.subject
                    if parent.type:
                        obj.type = parent.type
                    obj.save()
        else:
            ch_data = form.changed_data
            if obj.is_folder:
                obj.save()
            else:
                if not obj.is_copy():
                    if 'title' in ch_data:
                        obj.change_doc_vk_title()
                    obj.save()

    def delete_model(self, request, obj):
        if obj.is_folder:
            offers = obj.offers
            if offers:
                offers.update(folder=obj.parent)
        else:
            if not obj.is_copy():
                obj.delete_doc_from_vk()
        obj.delete()


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_folder_ancestors_names', 'subject', 'type', 'doc_created_bool')
    list_display_links = list_display
    readonly_fields = ('user', 'title', 'get_folder_ancestors_names', 'subject', 'type', 'comment',
                       'upload_dt', 'doc_created')
    list_filter = ('subject', 'type')
    search_fields = ('=subject__short_title', 'title')
    ordering = ['-doc_created', '-upload_dt']
    change_form_template = 'docs/admin_doc_change_view.html'
    change_list_template = 'docs/admin_offer_change_list.html'

    def changelist_view(self, request, extra_context=None):
        if request.GET.get('all'):
            url = request.build_absolute_uri('?')
            title = 'Показать МОИ'
        else:
            url = request.build_absolute_uri('?') + '?all=1'
            title = 'Показать ВСЁ'
        extra_context = extra_context or {}
        extra_context['custom_object_tools_items'] = [{'title': title, 'url': url}]
        return super(OfferAdmin, self).changelist_view(request, extra_context)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj:
            if not obj.doc_created:
                context['custom_buttons'] = [{'title': 'Добавить документ', 'action': '_add_doc_by_offer'}]
            download_url = obj.get_vk_download_url()
            if download_url:
                context['custom_object_tools_items'] = [{'title': 'Посмотреть документ', 'url': download_url}]
        return super(OfferAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def response_change(self, request, obj):
        if '_add_doc_by_offer' in request.POST:
            return redirect(f'/admin/docs/doc/add/?offer={obj.id}')
        return super(OfferAdmin, self).response_change(request, obj)

    def get_fieldsets(self, request, obj=None):
        return (
            (None, {'fields': ('title', 'comment', 'upload_dt')}),
            (None, {'fields': ('get_folder_ancestors_names', 'subject', 'type')}),
            (None, {'fields': ('user', 'doc_created')})
        )

    def has_change_permission(self, request, obj=None):
        if '_add_doc_by_offer' in request.POST:
            return True
        else:
            return False

    def get_queryset(self, request):
        if 'all' not in request.GET:
            top_folder = request.user.top_folder
            if top_folder:
                return Offer.objects.filter(folder__in=top_folder.get_descendants(include_self=True))
        return Offer.objects.all()

    def has_delete_permission(self, request, obj=None):
        if obj:
            top_folder = request.user.top_folder
            if top_folder:
                if obj.folder.is_descendant_of(top_folder, include_self=True):
                    return True
        else:
            if 'all' not in request.GET:
                return True
        return False


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display_links = list_display = ('id', 'title', 'short_title')
    ordering = ['short_title']


@admin.register(DocFolderType)
class DocFolderTypeAdmin(admin.ModelAdmin):
    list_display_links = list_display = ('id', 'title', 'title_plural')
    ordering = ['title']
