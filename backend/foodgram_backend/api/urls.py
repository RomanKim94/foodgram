from django.urls import include, path
from rest_framework import routers

from .views import AccountViewSet, ProductViewSet, RecipeViewSet, TagViewSet

app_name = 'api'

router = routers.SimpleRouter()
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)
router.register('ingredients', ProductViewSet)
router.register('users', AccountViewSet)


urlpatterns = [
    path(r'^auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
