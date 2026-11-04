from typing import ClassVar

from django.contrib import admin

from surveys.models import Placette, PlacetteLevel, PlacetteNode, PlacetteSurvey


class PlacetteLevelInline(admin.TabularInline):
    model = PlacetteLevel
    extra = 0
    fields = ("name", "parent_level", "order", "has_coordinates", "min_instances", "max_instances", "is_active")
    show_change_link = True


class PlacetteNodeInline(admin.TabularInline):
    model = PlacetteNode
    extra = 0
    fields = ("level", "parent", "label", "lat", "lon", "is_active")
    show_change_link = True


@admin.register(PlacetteLevel)
class PlacetteLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "placette_survey", "parent_level", "order", "has_coordinates", "activity_icon")
    list_filter = ("is_active", "placette_survey", "has_coordinates")
    search_fields = ("name",)
    fields = (
        "placette_survey",
        "parent_level",
        "name",
        "order",
        "has_coordinates",
        "min_instances",
        "max_instances",
        "json_schema",
        "is_active",
    )


@admin.register(PlacetteSurvey)
class PlacetteSurveyAdmin(admin.ModelAdmin):
    list_display = ("name", "organisation", "pole", "is_published", "activity_icon")
    list_filter = ("is_published", "is_active", "organisation")
    search_fields = ("name",)
    inlines: ClassVar = [PlacetteLevelInline]


@admin.register(Placette)
class PlacetteAdmin(admin.ModelAdmin):
    list_display = ("label", "lat", "lon", "activity_icon")
    list_filter = ("is_active", "surveys")
    search_fields = ("label",)
    filter_horizontal = ("surveys",)
    inlines: ClassVar = [PlacetteNodeInline]
