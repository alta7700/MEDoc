from tempfile import NamedTemporaryFile

import requests
from django.core.files import File

from .bot_funcs import *
from .vk_connection import *
from vk_api.bot_longpoll import VkBotEventType


def find_or_create_user_by_vk_id(vk_id):
    try:
        user = User.objects.get(id_vk=vk_id)
        created = False
    except User.DoesNotExist:
        user_kwargs = {
            'first_name': '',
            'last_name': '',
            'sex': User.NO_SEX,
            'avatar': None,
            'id_vk': vk_id
        }
        try:
            user_info = user_session.method('users.get', {
                'user_ids': str(vk_id),
                'fields': 'sex'
            })
            if user_info:
                user_info = user_info[0]
                user_kwargs['first_name'] = user_info.get('first_name', '')
                user_kwargs['last_name'] = user_info.get('last_name', '')
                sex = user_info.get('sex') or User.NO_SEX
                if sex == 1:
                    sex = User.WOMAN
                elif sex == 2:
                    sex = User.MAN
                user_kwargs['sex'] = sex
        except:
            pass
        user = User.objects.create_user(username=vk_id, **user_kwargs)
        created = True
    return user, created


def cached_vk_id_user(vk_id):
    vk_temp, created = VkTempValue.objects.select_related('user', 'current_folder').get_or_create(vk_id=vk_id)
    user_created = False
    if created:
        user, user_created = find_or_create_user_by_vk_id(vk_id)
        vk_temp.user = user
        vk_temp.current_folder = user.last_folder_in_bot
        vk_temp.save()
    return vk_temp, user_created


def message_new(message):
    vk_id = message['from_id']
    msg = message['text']
    payload = message.get('payload')
    attachments = message.get('attachments')
    vk_temp, user_created = cached_vk_id_user(vk_id)
    if user_created:
        start_work(vk_id)
    elif vk_temp.captcha == 'w':
        vk_temp.captcha = msg.strip()
        vk_temp.save(update_fields=['captcha'])
    elif payload:
        crop_payload = payload[11:-2]
        btn_func = crop_payload.split('-')[0].split('_')
        try:
            btn_pars = crop_payload.split('-')[1].split('_')
        except IndexError:
            btn_pars = None
        if btn_func[0] == 'folder':
            get_folder_to_show(vk_temp, btn_pars[0])
        elif btn_func[0] == 'doc':
            if len(btn_func) == 1:
                send_doc(vk_temp, btn_pars[0])
            else:
                if btn_func[1] == 'all':
                    send_doc_from_folder(vk_temp, btn_pars[0])
        elif btn_func[0] == 'set':
            if btn_func[1] == 'faculty':
                if btn_pars:
                    set_faculty(vk_temp, int(btn_pars[0]))
                else:
                    send_kb_set_faculty(vk_temp)
            elif btn_func[1] == 'course':
                if btn_pars:
                    set_course(vk_temp, int(btn_pars[0]))
                else:
                    send_kb_set_course(vk_temp)
        elif payload == '{"command":"start"}':
            start_work(vk_id)
    else:
        if vk_temp.user:
            if attachments:
                create_offer(vk_temp, attachments, msg, message['conversation_message_id'])
        if msg.lower() == 'начать':
            start_work(vk_id)


def run_vk_bot():
    longpoll = MyVkBotLongPoll(gr_session, VK_INT_GROUP_ID)
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.object.message
            if event.from_user:
                message_new(message)
