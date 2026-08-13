from django import forms
from django.contrib import admin
from easymde.widgets import EasyMDEEditor
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import BindingTariffInformation
from .models import TariffCodeDetail
from .models import TariffNode

# Register your models here.


class TariffCodeDetailForm(forms.ModelForm):
    class Meta:
        model = TariffCodeDetail
        fields = ("tariff_node", "tax_rate", "measurement_unit", "notes")
        widgets = {"notes": EasyMDEEditor}


class BindingTariffInformationForm(forms.ModelForm):
    """Form for BindingTariffInformation with validation and help text."""

    class Meta:
        model = BindingTariffInformation
        fields = ("tariff_node", "binding_number", "valid_from", "reasoning", "description")
        widgets = {
            "binding_number": forms.TextInput(
                attrs={
                    "placeholder": "TR + 14 digits (e.g., TR340000250097)",
                    "pattern": "^TR\\d{12}$",
                },
            ),
            "reasoning": EasyMDEEditor,
            "description": EasyMDEEditor,
        }


@admin.register(TariffNode)
class TariffNodeAdmin(TreeAdmin):
    list_display = ("name", "code")
    form = movenodeform_factory(TariffNode)
    search_fields = ("code", "name")

    def get_search_results(self, request, queryset, search_term):
        # 1. Fetch the default filtered queryset from Django's search engine
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # 2. Modify the string representation of objects *just* for the active AJAX request
        if "autocomplete" in request.path:
            for obj in queryset:
                # Calculate indentation visual markers based on the treebeard depth field
                # indent = "*" * (obj.depth - 1)
                obj.__class__.__str__ = lambda self: f"{'- ' * (self.depth - 1)} {self.code or ' '} {self.name}"

        return queryset, use_distinct


@admin.register(TariffCodeDetail)
class CustomTariffCodeAdmin(admin.ModelAdmin):
    form = TariffCodeDetailForm
    list_display = (
        "tariff_node",
        "tax_rate",
        "created_at",
    )
    search_fields = ("tariff_node__code", "tariff_node__name", "notes")
    autocomplete_fields = ("tariff_node",)


@admin.register(BindingTariffInformation)
class BindingTariffInformationAdmin(admin.ModelAdmin):
    form = BindingTariffInformationForm
    list_display = (
        "binding_number",
        "tariff_node",
        "valid_from",
        "created_at",
    )
    list_filter = ("valid_from", "created_at")
    search_fields = ("binding_number", "tariff_node__code", "tariff_node__name")
    autocomplete_fields = ("tariff_node",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Binding Information",
            {
                "fields": (
                    "tariff_node",
                    "binding_number",
                    "valid_from",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "reasoning",
                    "description",
                )
            },
        ),
    )

    def node_type(self, obj):
        """Display the node type of the associated tariff node."""
        return obj.tariff_node.get_node_type_display() if obj.tariff_node else "-"

    node_type.short_description = "Node Type"
