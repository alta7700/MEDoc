from MEDoc.celery import app
from .vk_bot.vk_main import message_new
from .models import VkTempValue
from datetime import datetime, timedelta


@app.task
def answer_message(event_type, obj):
    if event_type == 'message_new':
        message_new(obj)


@app.task
def delete_beat_temp_values_for_vk_users():
    old_v = VkTempValue.objects.filter(last_q_time__lte=(datetime.now() - timedelta(minutes=20)))
    for v in old_v:
        if v.user:
            user = v.user
            user.last_folder_in_bot = v.current_folder
            user.save()
        v.delete()

