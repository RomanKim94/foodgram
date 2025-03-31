from django.http import HttpResponseRedirect
from django.urls import reverse


def short_link_reverse(request, recipe_id):
    return HttpResponseRedirect(
        reverse('api:recipe-detail', args=[recipe_id])
    )
