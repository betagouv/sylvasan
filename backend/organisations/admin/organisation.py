from django import forms
from django.contrib import admin

from surveys.models import VocabularyCategory

from organisations.models import Organisation


class OrganisationAdminForm(forms.ModelForm):
    vocabulary_categories = forms.MultipleChoiceField(
        choices=VocabularyCategory.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Catégories de vocabulaire accessibles",
    )

    class Meta:
        model = Organisation
        fields = "__all__"


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name",)
    form = OrganisationAdminForm
