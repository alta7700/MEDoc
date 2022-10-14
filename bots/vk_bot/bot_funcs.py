import string
from random import choice
from docs.models import Doc, Offer
from .vk_connection import *
from profiles.models import User, Faculty


def start_work(vk_id: int) -> None:
    var_message(
        vk_id,
        'Привет, я неофициальный бот КубГМУ, сделанный студентами для студентов.\n'
        'Выбери свой факультет, чтобы тебе было проще пользоваться мной',
        kb_params=get_kb_set_faculty()
    )


def get_kb_set_faculty():
    kb = {}
    for i, faculty in enumerate(Faculty.objects.all(), start=1):
        kb[i] = ((faculty.short_title, 'primary', f'{{"button":"set_faculty-{faculty.id}"}}'),)
    return kb


def get_kb_set_course(faculty: Faculty):
    kb = {}
    for course in range(1, faculty.years + 1):
        kb[course] = ((f'{course} курс', 'primary', f'{{"button":"set_course-{course}"}}'),)
    return kb


def send_kb_set_faculty(vk_temp: VkTempValue):
    var_message(vk_temp.vk_id, 'Выбери свой факультет', kb_params=get_kb_set_faculty())


def set_faculty(vk_temp: VkTempValue, faculty_id: int):
    user: User = vk_temp.user
    faculty = Faculty.objects.get(id=faculty_id)
    user.faculty = faculty
    user.save()
    var_message(vk_temp.vk_id, 'Теперь выбери свой курс', kb_params=get_kb_set_course(faculty))


def send_kb_set_course(vk_temp: VkTempValue):
    user: User = vk_temp.user
    if not user.faculty:
        return send_kb_set_faculty(vk_temp)
    var_message(vk_temp.vk_id, 'Выбери свой курс', kb_params=get_kb_set_course(user.faculty))


def set_course(vk_temp: VkTempValue, course: int):
    user: User = vk_temp.user
    user.course = course
    user.save()
    get_folder_to_show(vk_temp, 'home')


def ask_reg_code(vk_temp) -> None:
    if vk_temp.user:
        var_message(vk_temp.vk_id, 'Ты уже авторизован')
        show_start_folders(vk_temp)
        return

    def create_code():
        new_c = ''.join((choice(string.ascii_letters + '0123456789012345678901234567890123456789') for _ in range(8)))
        if VkTempValue.objects.filter(code=new_c):
            return create_code()
        return new_c

    vk_temp.code = create_code()
    vk_temp.save()
    var_message(vk_temp.vk_id, vk_temp.code)


def fill_f_and_d_in_kb(f_and_d: list, btn_in_line: int, first_line=None):
    f_title_list = []
    d_title_list = []
    if first_line:
        kb = {1: [first_line], 2: []}
        num = 2
    else:
        kb = {1: []}
        num = 1
    for p in f_and_d:
        if p[0] == 'f':
            kb[num].append((f"{p[1]}){p[2][:30]}", 'secondary', f'{{"button":"folder-{p[3]}"}}'))
            f_title_list.append(f"{p[1]}) {p[2]}")
        else:
            kb[num].append((f"{p[1]}){p[2][:30]}", 'positive', f'{{"button":"doc-{p[3]}"}}'))
            d_title_list.append(f"{p[1]}) {p[2]}")
        if len(kb[num]) == btn_in_line:
            num += 1
            kb[num] = []
    if not kb[num]:
        del kb[num]
        num -= 1
    return kb, num, f_title_list, d_title_list


def get_folder_to_show(vk_temp, folder_id):
    if folder_id == 'home':
        user = vk_temp.user
        folder_ext = '0'
        if user.faculty:
            folder_ext = str(user.faculty.id)
            if user.course:
                folder_ext = f'{folder_ext}.{str(user.course)}'
        if folder_ext == '0':
            show_start_folders(vk_temp)
        else:
            try:
                folder = Doc.objects.get(ext=folder_ext)
                show_inner(vk_temp, folder, to_begin=True)
            except Doc.DoesNotExist:
                show_start_folders(vk_temp)
    elif folder_id == 'start':
        show_start_folders(vk_temp)
    elif folder_id == 'initial':
        show_start_folders(vk_temp)
    else:
        folder = Doc.objects.get(id=folder_id)
        show_inner(vk_temp, folder, to_begin=False)


def show_start_folders(vk_temp) -> None:
    folders = Doc.objects.filter(level=0).order_by('is_folder', 'id')

    f_and_d = []
    docs_count = 0
    for i, fd in enumerate(folders):
        if fd.is_folder:
            f_and_d.append(('f', i+1, fd.title, fd.id))
        else:
            docs_count += 1
            f_and_d.append(('d', i+1, fd.title, fd.vk_doc_id))

    kb, num, f_title_list, d_title_list = fill_f_and_d_in_kb(f_and_d, 1 if len(f_and_d) < 9 else 2)
    kb = {0: [('Изменить Факультет', 'primary', '{"button":"set_faculty"}')], **kb}

    f_titles = "Папки:\n" + "\n".join(f_title_list) if f_title_list else ""
    d_titles = "\n\nФайлы:\n" + "\n".join(d_title_list) if d_title_list else ""
    var_message(vk_temp.vk_id, f_titles + d_titles, kb_params=kb)

    vk_temp.current_folder = None
    vk_temp.save()


def show_inner(vk_temp, folder: Doc, to_begin=False) -> None:
    inner = list(folder.children.order_by('is_folder', 'title'))
    f_and_d = []
    if not inner:
        if to_begin:
            show_start_folders(vk_temp)
        else:
            reply_msg = f'Папка "{folder.title}" пока пустая, но ты можешь отправить мне документы)), '\
                        f'которые ты хочешь сюда добавить.\nАдмины порешают'
            if folder.level == 1:
                if not folder.admins.all():
                    reply_msg = f'У этого курса ещё нет администратора, староста курса пока не связывался с ' \
                                f'[id39398636|Создателем] по этому поводу'
            var_message(vk_temp.vk_id, reply_msg)
            vk_temp.current_folder = folder
            vk_temp.save()
        return

    docs_count = 0
    for i, fd in enumerate(inner):
        if fd.is_folder:
            f_and_d.append(('f', i+1, fd.title, fd.id))
        else:
            docs_count += 1
            f_and_d.append(('d', i+1, fd.title, fd.vk_doc_id))

    if docs_count > 1:
        all_docs_btn = ('Все документы', 'primary', f'{{"button":"doc_all-{folder.id}"}}')
        if len(f_and_d) <= 8:
            btn_in_line = 1
        elif len(f_and_d) <= 16:
            btn_in_line = 2
        elif len(f_and_d) <= 24:
            btn_in_line = 3
        else:
            btn_in_line = 4
    else:
        all_docs_btn = None
        if len(f_and_d) <= 9:
            btn_in_line = 1
        elif len(f_and_d) <= 18:
            btn_in_line = 2
        elif len(f_and_d) <= 27:
            btn_in_line = 3
        else:
            btn_in_line = 4

    kb, num, f_title_list, d_title_list = fill_f_and_d_in_kb(f_and_d, btn_in_line, all_docs_btn)
    num += 1
    kb[num] = []

    parent = folder.parent
    if parent:
        kb[num].append(('<-Назад', 'negative', f'{{"button":"folder-{parent.id}"}}'))
        if not to_begin:
            kb[num].append(('В начало', 'primary', '{"button":"folder-home"}'))
    else:
        kb[num].append(('<-Назад', 'negative', '{"button":"folder-start"}'))
        kb = {0: [('Изменить Курс', 'primary', '{"button":"set_course"}')], **kb}

    f_titles = "\n\nПапки:\n" + "\n".join(f_title_list) if f_title_list else ""
    d_titles = "\n\nФайлы:\n" + "\n".join(d_title_list) if d_title_list else ""
    var_message(vk_temp.vk_id, f"{folder.get_ancestors_names()}{f_titles}{d_titles}", kb_params=kb)
    vk_temp.current_folder = folder
    vk_temp.save()


def send_doc(vk_temp, doc_id):
    var_message(vk_temp.vk_id, attach_list=[f'doc{VK_STR_GROUP_ID}_{doc_id}'])


def send_doc_from_folder(vk_temp, folder_id):
    if vk_temp.current_folder.id != folder_id:
        folder = Doc.objects.get(id=folder_id)
        vk_temp.current_folder = folder
        vk_temp.save()
    docs = vk_temp.current_folder.children.filter(is_folder=False)
    attach_list = []
    for i, d in enumerate(docs):
        attach_list.append(f"doc{VK_STR_GROUP_ID}_{d.vk_doc_id}")
        if (i + 1) % 10 == 0:
            var_message(vk_temp.vk_id, attach_list=attach_list)
            attach_list = []
    if attach_list:
        var_message(vk_temp.vk_id, attach_list=attach_list)


def create_offer(vk_temp, attachments, comment, conv_mes_id):
    folder = vk_temp.current_folder
    offers_created = ''
    for i, attach in enumerate(attachments):
        if attach['type'] == 'doc':
            a = attach['doc']
            Offer(
                user=vk_temp.user,
                title=a['title'],
                folder=folder,
                subject=folder.subject,
                type=folder.type,
                comment=comment,
                conv_mes_id=conv_mes_id,
                index_in_message=i
            ).save()
            offers_created += f'\n{a["title"]}'
    var_message(vk_temp.vk_id, f'Заявки созданы:{offers_created}' if offers_created else 'Не вижу ни одного документа')
