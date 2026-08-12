from django import forms
from django.contrib import admin
from django.forms import ChoiceField
from django.forms import ModelForm
from treebeard.admin import TreeAdmin
from treebeard.forms import MoveNodeForm
from treebeard.forms import TreeNodeChoiceField
from treebeard.forms import movenodeform_factory

from .models import TariffCodeDetail
from .models import TariffNode

# Register your models here.


class TariffCodeDetailForm(forms.ModelForm):
    class Meta:
        model = TariffCodeDetail
        fields = "__all__"
        widgets = {
            "notes": forms.Textarea(attrs={"class": "vLargeTextField markdown-editor"}),
        }

    class Media:
        css = {
            "all": (
                "https://cdn.jsdelivr.net/npm/simplemde@1.11.2/dist/simplemde.min.css",
            )
        }
        js = (
            "https://cdn.jsdelivr.net/npm/simplemde@1.11.2/dist/simplemde.min.js",
            "/static/dj_tariff/js/markdown_admin_init.js",
        )


@admin.register(TariffNode)
class TariffNodeAdmin(TreeAdmin):
    list_display = ("name", "code")
    form = movenodeform_factory(TariffNode)
    search_fields = ("code", "name")

    def get_search_results(self, request, queryset, search_term):
        # 1. Fetch the default filtered queryset from Django's search engine
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # 2. Modify the string representation of objects *just* for the active AJAX request
        if "autocomplete" in request.path:
            for obj in queryset:
                # Calculate indentation visual markers based on the treebeard depth field
                indent = "*" * (obj.depth - 1)
                obj.__class__.__str__ = lambda self: (
                    f"{indent} : {self.code or ' '} {self.name}"
                )

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
    list_filter = ("measurement_unit",)
    autocomplete_fields = ("tariff_node",)
