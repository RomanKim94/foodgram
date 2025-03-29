import json
import os

from django.conf import settings
from django.db.models import Model


class CommandMixin:
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
                        [self.model(**item)
                         for item in json.load(file)],
                        ignore_conflicts=True,
                    )
                )
        except FileNotFoundError:
            self.stdout.write(f'Файл {file_path} не найден.')
        except Exception as exep:
            self.stdout.write(
                f'Во время импорта ингредиентов произошла ошибка: {exep}'
            )
        else:
            self.stdout.write(
                f'Успешно загружено {created_ingredient_count} '
                f'{self.model._meta.verbose_name_plural}'
            )
