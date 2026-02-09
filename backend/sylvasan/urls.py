from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path, re_path

urlpatterns = [
    path(f"{settings.ADMIN_URL}/", admin.site.urls),
]
urlpatterns.append(re_path(r"", include("users.urls")))
