from .tasks import answer_message
import json
from django.http import HttpResponse
from MEDoc.settings import VK_CALLBACK_SECRET_KEY, VK_CALLBACK_CONFIRMATION_CODE, VK_INT_GROUP_ID
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta


@csrf_exempt
def index_vk(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print(data)
        if data['secret'] == VK_CALLBACK_SECRET_KEY and data['group_id'] == VK_INT_GROUP_ID:
            if data['type'] == 'message_new':
                message = data['object']['message']
                if datetime.now() - datetime.fromtimestamp(message['date']) < timedelta(seconds=7):
                    answer_message.delay('message_new', message)
                return HttpResponse('OK', content_type="text/plain", status=200)
            elif data['type'] == 'confirmation':
                return HttpResponse(VK_CALLBACK_CONFIRMATION_CODE, content_type="text/plain", status=200)
    return HttpResponse('ты что такое')
