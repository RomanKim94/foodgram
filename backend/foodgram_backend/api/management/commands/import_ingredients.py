from django.core.management.base import BaseCommand
from recipes.models import Product

from .base_command_mixin import CommandMixin


class Command(CommandMixin, BaseCommand):
    model = Product
