from django.urls import include, path, re_path
from rest_framework import routers

from .views import ProductViewSet, RecipeViewSet, TagViewSet, UserViewSet

router = routers.SimpleRouter()
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)
router.register('ingredients', ProductViewSet)
router.register('users', UserViewSet)


urlpatterns = [
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
