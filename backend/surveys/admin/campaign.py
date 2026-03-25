from django.contrib import admin

from surveys.models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "organisation", "pole", "start_date", "end_date")
