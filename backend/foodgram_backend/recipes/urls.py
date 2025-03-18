from django.urls import include, path
from rest_framework import routers

from . import constants as const
from .views import IngredientViewSet, RecipeViewSet, TagViewSet

router = routers.SimpleRouter()
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path(
        f'{const.SHORT_LINK_SIGN}/<str:url_slug>/',
        RecipeViewSet.as_view({'get': 'retrieve'}),
    )
]
