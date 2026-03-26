from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin

from surveys.models import Campaign


@admin.register(Campaign)
class CampaignAdmin(SimpleHistoryAdmin):
    list_display = ("title", "organisation", "pole", "start_date", "end_date")
