from django.contrib import admin
from django.contrib.auth.models import Group

from .user import UserAdmin


def get_admin_header():
    return "SylvaSan"


admin.site.site_header = get_admin_header()
admin.site.site_title = get_admin_header()
admin.site.unregister(Group)
