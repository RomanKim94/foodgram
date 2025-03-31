from recipes.models import Product

from .base_command_mixin import Command


class Command(Command):
    model = Product
