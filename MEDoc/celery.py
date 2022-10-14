import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MEDoc.settings')

app = Celery('MEDoc')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'clean-cache-every-1-minute': {
        'task': 'bots.tasks.delete_beat_temp_values_for_vk_users',
        'schedule': crontab(minute='*/1'),
    },
    'rebuild-tree-every-5-minute': {
        'task': 'docs.tasks.rebuild_trees',
        'schedule': crontab(minute='*/5')
    }
}