from django.conf import settings
from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from opensearch_filtering.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)

app_name = "api"
urlpatterns = router.urls

# Include opensearch app URLs
urlpatterns += [
    path("", include("opensearch_filtering.opensearch.urls", namespace="opensearch")),
]
