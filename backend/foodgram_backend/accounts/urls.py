from django.urls import include, path, re_path
from rest_framework import routers
from djoser import views
from accounts.views import UserViewSet


router = routers.SimpleRouter()
router.register('', UserViewSet)


urlpatterns = [
    re_path(r'^me/$', views.UserViewSet.as_view({'get': 'me'})),
    re_path(r'^set_password/$', views.UserViewSet.as_view(
        {'post': 'set_password'},
    )),
    path('', include(router.urls)),
]
