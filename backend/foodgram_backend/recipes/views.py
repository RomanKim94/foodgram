from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def short_link_reverse(request, recipe_id):
    get_object_or_404(Recipe, pk=recipe_id)
    return redirect('api:recipe-detail', recipe_id)
