import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.keyboard import VkKeyboard
from vk_api.exceptions import Captcha
from vk_api.upload import VkUpload
from bots.models import VkTempValue
from io import BytesIO
from MEDoc.settings import VK_USER_TK, VK_GROUP_TK, VK_INT_GROUP_ID, VK_API_VERSION, VK_APP_ID, VK_STR_GROUP_ID
from time import sleep


class MyVkApi(vk_api.VkApi):
    RPS_DELAY = 0.25


gr_session = MyVkApi(token=VK_GROUP_TK, app_id=VK_APP_ID, api_version=VK_API_VERSION)
user_session = MyVkApi(token=VK_USER_TK, app_id=VK_APP_ID, api_version=VK_API_VERSION)
SITE_URL = 'https://kub-medoc.ru/'


class MyVkBotLongPoll(VkBotLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                print('TimeOut', e)


upload = VkUpload(gr_session)


def var_message(user_id=None, text=None, kb_params=None, kb_inline=False, attach_list=None, user_ids=None):
    values = {
        'user_id': user_id,
        'random_id': 0
    }
    if user_ids:
        values = {
            'user_ids': user_ids,
            'random_id': 0
        }
    if text:
        values['message'] = text
    if kb_params:
        keyboard = VkKeyboard(inline=kb_inline)
        lines_count = len(kb_params.values())
        for i, line in enumerate(list(kb_params.values())):
            for btn in line:
                if isinstance(btn, dict):
                    if btn['type'] == 'link':
                        keyboard.add_openlink_button(*btn['btn'])
                else:
                    keyboard.add_button(*btn)
            if i + 1 != lines_count:
                keyboard.add_line()
        values['keyboard'] = keyboard.get_keyboard()
    if attach_list:
        values['attachment'] = ','.join(attach_list)
    try:
        gr_session.method("messages.send", values)
    except vk_api.exceptions.ApiError:
        gr_session.method("messages.send", values)


def send_captcha_to_user(user, captcha, wrong=False):
    vk_temp, created = VkTempValue.objects.get_or_create(vk_id=user.id_vk)
    vk_id = vk_temp.vk_id

    if vk_temp.captcha != '':
        while vk_temp.captcha != '':
            sleep(5)
            vk_temp.refresh_from_db()
    vk_temp.captcha = 'w'
    vk_temp.save()

    cap_image = upload.photo_messages([BytesIO(captcha.get_image())], vk_id)[0]
    cap_image = f'photo{cap_image.get("owner_id")}_{cap_image.get("id")}_{cap_image.get("access_key")}'
    var_message(vk_id, 'Неправильно, давай заново' if wrong else 'Отправь код с картинки', attach_list=[cap_image])
    while vk_temp.captcha == 'w':
        sleep(5)
        vk_temp.refresh_from_db()
    try:
        captcha_input = vk_temp.captcha
        vk_temp.captcha = ''
        vk_temp.save()
        return captcha.try_again(captcha_input)
    except Captcha as C:
        return send_captcha_to_user(user, C, wrong=True)
