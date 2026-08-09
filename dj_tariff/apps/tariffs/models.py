from django.db import models

# Create your models here.
from treebeard.mp_tree import MP_Node


class TariffNode(MP_Node):
    class NodeType(models.TextChoices):
        SECTION = "SECTION", "Bölüm"
        CHAPTER = "CHAPTER", "Fasıl"
        HEADING = "HEADING", "Pozisyon"
        SUBHEADING = "SUBHEADING", "Alt Pozisyon"
        GTIP = "GTIP", "Gtip"

    code = models.CharField(
        max_length=12,
        db_index=True,
        blank=True,
        null=True,
        help_text="Unformatted code (e.g., 010121000000). Null for Sections.",
    )
    name = models.TextField(help_text="Official Turkish description")
    node_type = models.CharField(max_length=15, choices=NodeType.choices)

    # Materialized path ordered by code
    node_order_by = ["code"]

    class Meta:
        verbose_name = "Tariff Node"
        verbose_name_plural = "Tariff Nodes"
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["node_type"]),
        ]

    def __str__(self):
        return f"{self.code or 'SECTION'} - {self.name[:50]}"
