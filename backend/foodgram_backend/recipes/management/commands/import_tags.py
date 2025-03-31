from recipes.models import Tag

from .base_command import Command


class Command(Command):
    model = Tag
