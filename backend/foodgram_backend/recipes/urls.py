from django.urls import path
from django.views.generic.base import RedirectView

urlpatterns = [
    path(
        's/<int:pk>/',
        RedirectView.as_view(
            pattern_name='api:recipe-detail',
            permanent=False
        ),
        name='short_link',
    ),
]
