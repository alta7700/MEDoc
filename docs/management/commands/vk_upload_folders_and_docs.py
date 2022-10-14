from abc import ABC
from django.core.management.base import BaseCommand
import requests
import vk_api
from vk_api.exceptions import Captcha
from os import startfile
from pathlib import Path
from docs.models import Doc
from profiles.models import Faculty
from MEDoc.settings import VK_USER_TK, VK_API_VERSION, VK_APP_ID, VK_INT_GROUP_ID


user_session = vk_api.VkApi(token=VK_USER_TK, app_id=VK_APP_ID, api_version=VK_API_VERSION)


def captcha_input(captcha):
    with open('captcha.jpg', 'wb') as i:
        i.write(captcha.get_image())
    startfile('captcha.jpg')
    print(captcha.get_url())
    key = input()
    try:
        return captcha.try_again(key)
    except Captcha as C:
        return captcha_input(C)


faculties = {
    1: ('ЛЕЧ', 'Лечебный'),
    2: ('ПЕД', 'Педиатрический'),
    3: ('МПФ', 'Медико-профилактический'),
    4: ('СТОМ', 'Стоматологический'),
    5: ('ФАРМ', 'Фармакологический')
}


def parse_dir(path, lvl=0, parent_folder=None):
    for p in path.iterdir():
        if p.is_dir():
            # Папка первого уровня - это папка факультета (ext: '1', '2', '3', '4', '5')
            if lvl == 0:
                folder_title = p.name.split('.')[1].strip()
                folder_index = p.name.split('.')[0]
                if faculties[int(folder_index)][0] != folder_title:
                    raise Exception(F'Неправильный нейминг\n{", ".join([f"{i}. {n}" for i, n in faculties.items()])}')
                if not Faculty.objects.filter(short_title=faculties[int(folder_index)][1]):
                    fac = Faculty(title=faculties[int(folder_index)][1], short_title=faculties[int(folder_index)][0])
                    fac.save()
            # Папки второго уровня - папки курса (I-я цифра ext - от факультета; II-я цифра - № курса)
            elif lvl == 1:
                course_n = p.name[0]
                if not 1 <= int(course_n) <= 6 and p.name[1:] != ' Курс':
                    raise Exception(F'Неправильный нейминг\nКурс № {course_n}')
                folder_title = p.name
                folder_index = parent_folder.ext + course_n
            else:
                folder_title = p.name
                folder_index = ''

            folder = Doc(title=folder_title, is_folder=True, ext=folder_index, parent=parent_folder)
            folder.save()
            parse_dir(p, lvl+1, folder)
        else:
            add_file_to_vk(p, parent_folder)


def add_file_to_vk(doc, parent_folder):
    try:
        doc_ext = doc.name.split('.')[1]
    except IndexError:
        print(f'Нет расширения у файла {doc.name}')
        doc_ext = ''
    try:
        upload_url = user_session.method("docs.getUploadServer", {
            'group_id': VK_INT_GROUP_ID
        }).get('upload_url')
    except Captcha as c:
        upload_url = captcha_input(c)
    try:
        response = requests.post(upload_url, files={'file': open(doc, 'rb')}).json()
    except Captcha as c:
        response = captcha_input(c)
    try:
        upload_doc_info = user_session.method('docs.save', {
            'file': response.get('file')
        }).get('doc')
    except Captcha as c:
        upload_doc_info = captcha_input(c)
    try:
        vk_doc_id = upload_doc_info.get('id') if upload_doc_info.get('id') else upload_doc_info.get('doc').get('id')
    except Exception as e:
        print(e)
        vk_doc_id = None
    new_doc = Doc(
        title=doc.name,
        is_folder=False,
        ext=doc_ext,
        vk_doc_id=vk_doc_id,
        parent=parent_folder
    )
    new_doc.save()
    print(f"{new_doc.title} -> загружен ({new_doc.vk_doc_id})")


def validate_hierarchy(path, lvl=0):
    doc_count, folder_count = 0, 0
    for p in path.iterdir():
        if p.is_dir():
            if lvl == 0:
                folder_id = int(p.name.split('.')[0])
                folder_name = p.name.split('.')[1].strip()
                if faculties[folder_id][0] != folder_name:
                    raise Exception(F'Неправильный нейминг\n{", ".join([f"{i}. {n}" for i, n in faculties.items()])}')
            elif lvl == 1:
                course_n = int(p.name[0])
                if not 1 <= course_n <= 6 or p.name[1:] != ' курс':
                    raise Exception(F'Неправильный нейминг\nКурс № {course_n}')
            folder_count += 1
            validate_hierarchy(p, lvl+1)
        else:
            doc_count += 1
    if folder_count + doc_count > 30:
        raise Exception(f'Большая вложенность ({folder_count + doc_count}) в {path}')


def run_folders_processing():
    main_dir_path = (Path(__file__).parent.parent.parent / 'folders_and_docs')
    validate_hierarchy(main_dir_path)
    start_folder = Doc(
        title='КубГМУ',
        is_folder=True,
        ext='0',
        parent=None
    )
    start_folder.save()
    parse_dir(main_dir_path, parent_folder=start_folder)


class Command(BaseCommand, ABC):
    help = 'Выгрузка документов в вк'

    def handle(self, *args, **options):
        run_folders_processing()
