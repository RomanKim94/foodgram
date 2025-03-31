from recipes.models import Tag

from .base_command_mixin import Command


class Command(Command):
    model = Tag
