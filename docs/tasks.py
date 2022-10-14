import requests
from vk_api.exceptions import Captcha
from MEDoc.settings import VK_STR_GROUP_ID,  VK_INT_GROUP_ID
from MEDoc.celery import app
from bots.vk_bot.vk_connection import user_session, var_message, send_captcha_to_user
from .models import Doc, Offer
from profiles.models import User
from os import remove


@app.task
def download_doc_and_upload_vk(title=None, ext=None, parent=None, owner=None, offer=None, file=None):
    user = User.objects.get(id=owner)
    try:
        parent = Doc.objects.select_related('subject', 'type').get(id=parent)
        if offer:
            offer = Offer.objects.select_related('user').get(id=offer)
    except:
        var_message(user.id_vk, 'Что-то пошло нет так')
        return

    doc_db = Doc(
        title=title,
        ext=ext,
        is_folder=False,
        parent=parent,
        subject=parent.subject,
        type=parent.type,
        owner=user
    )

    doc_title = doc_db.get_vk_doc_title()

    if not file:
        doc_download_url = offer.get_vk_download_url()
        if doc_download_url:
            with open(doc_title, 'wb') as f:
                f.write(requests.get(doc_download_url).content)
        else:
            var_message(user.id_vk, 'Что-то пошло не так')
            return

    try:
        upload_url = user_session.method("docs.getUploadServer", {
            'group_id': VK_INT_GROUP_ID
        }).get('upload_url')
    except Captcha as C:
        var_message(39398636, f'Капча1 для [id{user.id_vk}|{user.first_name} {user.last_name}]')
        upload_url = send_captcha_to_user(user, C).get('upload_url')
    try:
        response = requests.post(upload_url, files={'file': open(doc_title, 'rb')}).json()
    except Captcha as C:
        var_message(39398636, f'Капча2 для [id{user.id_vk}|{user.first_name} {user.last_name}]')
        response = send_captcha_to_user(user, C)
    remove(doc_title)
    try:
        upload_doc_info = user_session.method('docs.save', {
            'file': response.get('file'),
            'title': doc_title
        }).get('doc')
    except Captcha as C:
        var_message(39398636, f'Капча3 для [id{user.id_vk}|{user.first_name} {user.last_name}]')
        upload_doc_info = send_captcha_to_user(user, C).get('doc')
    except:
        var_message(user.id_vk, 'Что-то пошло не так, вероятно документ заблокирован')
        return
    doc_db.vk_doc_id = upload_doc_info.get('id')
    doc_db.save()
    var_message(user.id_vk, 'Успешно добавлен', attach_list=[f'doc{VK_STR_GROUP_ID}_{doc_db.vk_doc_id}'])

    if offer:
        offer.doc_created = doc_db
        offer.save()
        kb = {1: ((parent.title, 'secondary', f'{{"button":"folder-{parent.id}"}}'), )}
        var_message(offer.user.id_vk, f'Документ, предложенный Вами, добавлен в папку {parent.get_ancestors_names()}. Спасибо☺',
                    kb_params=kb, kb_inline=True, attach_list=[f'doc{VK_STR_GROUP_ID}_{doc_db.vk_doc_id}'])


@app.task
def rebuild_trees():
    Doc.objects.rebuild()
