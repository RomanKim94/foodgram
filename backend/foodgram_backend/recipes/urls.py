from api.views import RecipeViewSet
from django.urls import path

urlpatterns = [
    path(
        '<int:recipe_id>/',
        RecipeViewSet.as_view({'get': 'retrieve'},),
        name='short_link'
    ),
]
