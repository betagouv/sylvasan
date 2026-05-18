from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _


@admin.register(get_user_model())
class UserAdmin(UserAdmin):
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("email", "first_name", "last_name")}),)

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "username",
    )
    show_facets = admin.ShowFacets.NEVER
    readonly_fields = ("dsf_last_claims",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "password",
                )
            },
        ),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                )
            },
        ),
        (
            _("Source"),
            {
                "fields": (
                    "source",
                    "external_id",
                ),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        (
            _("IGN/DSF"),
            {
                "fields": ("dsf_last_claims",),
            },
        ),
    )
