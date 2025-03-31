from django.urls import path

from .views import short_link_reverse

urlpatterns = [
    path(
        's/<int:recipe_id>/',
        short_link_reverse,
        name='short_link',
    ),
]
