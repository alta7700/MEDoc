from abc import ABC
from django.core.management.base import BaseCommand
from docs.tasks import rebuild_tree


class Command(BaseCommand, ABC):
    help = 'Упорядочить дерево'

    def handle(self, *args, **options):
        rebuild_tree()
