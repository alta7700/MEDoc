# Generated by Django 4.0.2 on 2022-03-07 13:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('docs', '0001_initial'),
        ('bots', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vktempvalue',
            name='current_folder',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='now_ids', to='docs.doc'),
        ),
        migrations.AddField(
            model_name='vktempvalue',
            name='favourites',
            field=models.ManyToManyField(to='docs.Doc', verbose_name='Редакт. избранного'),
        ),
    ]