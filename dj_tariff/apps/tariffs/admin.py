from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import TariffNode

# Register your models here.


@admin.register(TariffNode)
class TariffNodeAdmin(TreeAdmin):
    list_display = ("name", "code")
    form = movenodeform_factory(TariffNode)
    search_fields = ("name", "code")
