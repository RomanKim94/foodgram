from django.urls import include, path
from rest_framework import routers

from recipes.views import TagViewSet, RecipeViewSet, IngredientViewSet
from recipes import constants as const


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
