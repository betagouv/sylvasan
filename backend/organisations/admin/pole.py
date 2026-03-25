from django.contrib import admin

from organisations.models import Pole


@admin.register(Pole)
class PoleAdmin(admin.ModelAdmin):
    list_display = ("name", "organisation")
