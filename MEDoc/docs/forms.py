from django import forms
from mptt import forms as mptt_forms
from .models import Doc


class DocAdminForm(mptt_forms.MPTTAdminForm):

    class Meta:
        model = Doc
        fields = forms.ALL_FIELDS

    def __init__(self, *args, **kwargs):
        super(DocAdminForm, self).__init__(*args, **kwargs)
        self.fields['original'].queryset = Doc.objects.filter(is_folder=False)

    def clean(self):
        cleaned_data = super(DocAdminForm, self).clean()
        parent = cleaned_data.get('parent')
        if parent:
            if len(parent.get_children()) >= 24:
                self.add_error(
                    'title' if cleaned_data.get('title') else 'parent',  # title если parent скрыт и есть title
                    forms.ValidationError('В родительской папке не может находиться больше 24 папок и документов',
                                          code='invalid')
                )
        return self.cleaned_data


class EditDocAdminForm(DocAdminForm):

    def clean(self):
        cleaned_data = super(EditDocAdminForm, self).clean()
        instance = getattr(self, 'instance', None)
        parent = cleaned_data.get('parent')
        if parent:
            if instance:
                i_parent = instance.parent
                if parent.subject != i_parent.subject or parent.type != i_parent.type:
                    self.add_error(
                        'parent',
                        forms.ValidationError(
                            f'Предмет и тип новой папки должны совпадать с предметом и типом в текущей',
                            code='invalid'
                        )
                    )
        return self.cleaned_data


class DocAddByOfferForm(DocAdminForm):
    offer = forms.IntegerField(widget=forms.NumberInput(attrs={'type': 'hidden'}))

    class Meta:
        model = Doc
        fields = ('title', 'ext', 'parent', 'offer')


class AddCopyDocForm(DocAdminForm):

    class Meta:
        model = Doc
        fields = ('parent', 'original')

    def clean(self):
        cleaned_data = super(AddCopyDocForm, self).clean()
        orig = cleaned_data.get('original')
        parent = cleaned_data.get('parent')
        if parent:
            if parent.subject != orig.subject or parent.type != orig.type:
                subj_and_type = f'Предмет{f": {orig.subject.short_title}" if orig.subject else "а нет"}\n' \
                                f'Тип{f": {orig.type.title}" if orig.type else "а нет"}'
                self.add_error(
                    'parent',
                    forms.ValidationError(
                        f'Предмет и тип родительской папки должны совпадать с оригиналом\n{subj_and_type}',
                        code='invalid')
                )
        return self.cleaned_data


class InsertFolderAtFolderForm(DocAdminForm):

    class Meta:
        model = Doc
        fields = ('title', 'parent', 'subject', 'type')


class InsertDocAtFolderForm(DocAdminForm):
    doc_file = forms.FileField(label='Документ')

    class Meta:
        model = Doc
        fields = ('title', 'ext', 'doc_file', 'parent')


class EditFolderForm(EditDocAdminForm):

    class Meta:
        model = Doc
        fields = ('title', 'parent', 'subject', 'type', 'owner')


class EditCopyDocForm(EditDocAdminForm):

    class Meta:
        model = Doc
        fields = ('original', 'parent', 'subject', 'type', 'owner')


class EditOriginalDocForm(EditDocAdminForm):

    class Meta:
        model = Doc
        fields = ('title', 'ext', 'parent', 'subject', 'type', 'owner')
