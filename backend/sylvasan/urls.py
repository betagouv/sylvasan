from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path(f"platform/{settings.ADMIN_URL}/", admin.site.urls),
    path("platform/", include("users.urls")),
]
