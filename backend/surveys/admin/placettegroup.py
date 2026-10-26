from typing import ClassVar

from django.contrib import admin

from surveys.models import Placette, PlacetteGroup


class PlacetteInline(admin.TabularInline):
    model = Placette
    extra = 0
    fields = ("label", "lat", "lon", "characteristics", "is_active")
    show_change_link = True


@admin.register(PlacetteGroup)
class PlacetteGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "organisation", "pole", "is_published", "activity_icon")
    list_filter = ("is_published", "is_active", "organisation")
    search_fields = ("name",)
    inlines: ClassVar = [PlacetteInline]
