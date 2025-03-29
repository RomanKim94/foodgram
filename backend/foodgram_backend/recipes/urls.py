from django.urls import path

from api.views import RecipeViewSet

urlpatterns = [
    path(
        '<int:recipe_id>/',
        RecipeViewSet.as_view({'get': 'retrieve'},),
        name='short_link'
    ),
]
