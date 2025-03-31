from recipes.models import Product

from .base_command import Command


class Command(Command):
    model = Product
