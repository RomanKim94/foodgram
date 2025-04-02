from django.shortcuts import redirect
from rest_framework.exceptions import ValidationError

from .models import Recipe


def short_link_reverse(request, recipe_id):
    if Recipe.objects.filter(pk=recipe_id).exists():
        return redirect(f'/recipes/{recipe_id}')
    return ValidationError(f'Рецепта с {recipe_id=} не существует')
