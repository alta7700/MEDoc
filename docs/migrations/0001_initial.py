# Generated by Django 4.0.2 on 2022-03-07 13:17

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Doc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название')),
                ('ext', models.CharField(blank=True, max_length=15, verbose_name='Расширение файла')),
                ('is_folder', models.BooleanField(verbose_name='Это папка?')),
                ('vk_doc_id', models.PositiveBigIntegerField(blank=True, default=None, null=True, verbose_name='ID документа ВК')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
            ],
            options={
                'verbose_name': 'Документ',
                'verbose_name_plural': 'Документы',
            },
        ),
        migrations.CreateModel(
            name='DocFolderType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=40, verbose_name='Название')),
                ('title_plural', models.CharField(max_length=40, verbose_name='Мн. Название')),
            ],
            options={
                'verbose_name': 'Тип документа',
                'verbose_name_plural': 'Тип папки',
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Название')),
                ('short_title', models.CharField(max_length=20, unique=True, verbose_name='Краткое название')),
            ],
            options={
                'verbose_name': 'Предмет',
                'verbose_name_plural': 'Предметы',
                'ordering': ['short_title'],
            },
        ),
        migrations.CreateModel(
            name='Offer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название')),
                ('comment', models.TextField(blank=True, verbose_name='Комментарий')),
                ('vk_owner_id', models.BigIntegerField(editable=False, verbose_name='vk_owner_id')),
                ('vk_doc_id', models.BigIntegerField(editable=False, verbose_name='vk_doc_id')),
                ('vk_doc_access_key', models.CharField(editable=False, max_length=50, verbose_name='vk_doc_access_key')),
                ('upload_dt', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('doc_created', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='offered_from', to='docs.doc', verbose_name='Созданный документ')),
                ('folder', mptt.fields.TreeForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='docs.doc', verbose_name='Папка')),
                ('subject', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='docs.subject', verbose_name='Предмет')),
                ('type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='docs.docfoldertype', verbose_name='Тип')),
            ],
            options={
                'verbose_name': 'Предложение',
                'verbose_name_plural': 'Предложения',
                'ordering': ['subject', 'type'],
            },
        ),
    ]
