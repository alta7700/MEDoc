# Generated by Django 4.0.2 on 2022-03-13 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0004_alter_docfoldertype_title_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='offer',
            name='index_in_message',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Номер документа в сообщении'),
            preserve_default=False,
        ),
    ]
