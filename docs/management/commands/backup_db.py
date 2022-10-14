from pathlib import Path

import requests
import yadisk
import os
from datetime import datetime
from django.core.management import BaseCommand

from MEDoc import settings
from MEDoc.settings import VK_GROUP_OWNER_ID
from bots.vk_bot.vk_connection import gr_session, var_message


class Command(BaseCommand):
    help = 'Backup db'

    def handle(self, *args, **options):

        db_name = settings.DATABASES["default"]["NAME"]
        backup_filename = f'{datetime.now().strftime("%d-%m-%Y--%H-%M-%S")}.sql'
        backup_file = (Path(__file__).parent / 'backups' / backup_filename).as_posix()
        os.system(f'pg_dump -d {db_name} > {backup_file}')

        try:
            ya = yadisk.YaDisk(token=settings.YADISK_TOKEN)
            ya.upload(backup_file, f'/{db_name}Backup/{backup_filename}')
        except:
            upload_url = gr_session.method("docs.getMessagesUploadServer", {
                'peer_id': VK_GROUP_OWNER_ID
            }).get('upload_url')
            response = requests.post(upload_url, files={'file': open(backup_file, 'rb')}).json()
            doc = gr_session.method('docs.save', {
                'file': response.get('file')
            }).get('doc')
            attach = 'doc{}_{}'.format(doc.get('owner_id'), doc.get('id'))

            var_message(VK_GROUP_OWNER_ID, text='Я не смог сделать бэкап', attach_list=[attach, ])
