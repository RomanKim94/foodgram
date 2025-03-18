import json
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь до json файла с ингредиентами',
        )

    def handle(self, *args, **kwargs):
        Ingredient.objects.all().delete()
        file_path = kwargs['file_path']
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            objects = [Ingredient(**item) for item in data]
            Ingredient.objects.bulk_create(objects)
        self.stdout.write(f'Успешно загружено {len(objects)} ингредиентов')
