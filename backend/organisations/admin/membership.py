from django.contrib import admin

from organisations.models import Membership


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organisation", "pole", "membership_type")
