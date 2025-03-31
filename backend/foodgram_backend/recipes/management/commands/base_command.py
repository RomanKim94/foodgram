import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Model


class Command(BaseCommand):
    model: Model = None

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь от директории проекта до json файла с '
                 f'{self.model._meta.verbose_name_plural}',
        )

    def handle(self, *args, **kwargs):
        try:
            file_path = kwargs['file_path']
            full_file_path = os.path.join(settings.BASE_DIR, file_path)
            with open(full_file_path, 'r', encoding='utf-8') as file:
                created_ingredient_count = len(
                    self.model.objects.bulk_create(
                        (self.model(**item) for item in json.load(file)),
                        ignore_conflicts=True,
                    )
                )
            self.stdout.write(
                f'Успешно загружено {created_ingredient_count} '
                f'{self.model._meta.verbose_name_plural}'
            )
        except Exception as exception:
            self.stdout.write(
                f'Во время импорта {self.model._meta.verbose_name_plural} '
                f'из файла {file_path}'
                f'произошла ошибка: {exception}'
            )
