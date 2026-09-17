from typing import ClassVar

from django.contrib import admin, messages

from organisations.models import ApiKey


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display: ClassVar[list] = ["name", "prefix", "organisation", "is_active", "expires_at", "creation_date"]
    list_filter: ClassVar[list] = ["is_active", "organisation"]
    readonly_fields: ClassVar[list] = ["prefix", "creation_date"]
    fields: ClassVar[list] = ["name", "organisation", "expires_at", "is_active", "prefix"]

    def save_model(self, request, obj, form, change):
        if not change:
            raw_key, prefix, hashed_key = ApiKey.generate()
            obj.prefix = prefix
            obj.hashed_key = hashed_key
            obj.save()
            messages.success(
                request,
                f"Clé API générée (visible une seule fois — conservez-la) : {raw_key}",
            )
        else:
            obj.save()
