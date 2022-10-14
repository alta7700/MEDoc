from abc import ABC
from django.core.management.base import BaseCommand
from bots.vk_bot import vk_main


class Command(BaseCommand, ABC):
    help = 'ВК longpoll'

    def handle(self, *args, **options):
        vk_main.run_vk_bot()
