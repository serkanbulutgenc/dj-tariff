from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
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
        help_text="Unformatted code (e.g., 010121000000). Empty for Sections.",
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


class TariffCodeDetail(models.Model):
    class MeasurementUnit(models.TextChoices):
        GT = "GT", "Gross ton"
        CK = "c/k", "Karat (1 metrik karat=2*10-4 kg)"
        CE_EL = "ce/el", "Hücre adedi"
        CT_L = "ct/l", "Ton başına taşıma kapasitesi(1)"
        G = "g", "Gram"
        GI_F_S = "gi F/S", "Gram olarak fissile izotop"
        KG_H2O2 = "kg H2O2", "Kilogram olarak Hidrojen peroksit"
        KG_K2O = "kg K2O", "Kilogram olarak Potasyum oksit"
        KG_KOH = "kg KOH", "Kilogram olarak Potasyum hidroksit (kostik potas)"
        KG_MET_AM = "kg met.am.", "Kilogram olarak Metil aminler"
        KG_N = "kg N", "Kilogram olarak Azot"
        KG_NAOH = "Kg NaOH", "Kilogram olarak Sodyum hidroksit (kostik soda)"
        KG_NET_EDA = "kg/net eda", "Kilogram olarak kurutulmuş net ağırlık"
        KG_P2O5 = "kg P2O5", "Kilogram olarak Difosfor pentaoksit"
        KG_90_SDT = "kg %90 sdt", "Kilogram olarak % 90 kuru ürün"
        KG_U = "kg U", "Kilogram olarak Uranyum"
        THOUSAND_KWH = "1000 kWh", "1000 kilovat saat"
        L = "l", "Litre"
        KG_C5H14CINO = "Kg C5H14CINO", "Kilogram olarak Kolin klorür"
        L_ALC_100 = "l alc. %100", "Litre olarak saf alkol (%100)"
        M = "m", "Metre"
        M2 = "m2", "Metre kare"
        M3 = "m3", "Metre küp"
        THOUSAND_M3 = "1000 m3", "1000 Metre küp"
        P_A = "p/a", "Çift"
        P_ST = "p/st", "Adet"
        HUNDRED_P_ST = "100 p/st", "100 Adet"
        THOUSAND_P_ST = "1000 p/st", "1000 Adet"
        TJ = "TJ", "Terajul (Brüt kalori değeri)"
        T_CO2 = "t. CO2", "Ton CO2 (karbon dioksit) eşdeğeri"

    tariff_node = models.OneToOneField(
        TariffNode,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tariff_detail",
        help_text="Tariff node associated with this custom tariff metadata.",
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0.0,
        help_text="Tax rate as a percentage.",
    )
    measurement_unit = models.CharField(
        max_length=32,
        choices=MeasurementUnit.choices,
        help_text="Measurement unit for this tariff entry.",
    )
    notes = models.TextField(
        blank=True, help_text="Optional notes for this tariff entry."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tariff Detail"
        verbose_name_plural = "Tariff Details"
        ordering = ["tariff_node__code"]

    def __str__(self):
        return f"{self.tariff_node.code or self.tariff_node} - {self.tax_rate}%"
