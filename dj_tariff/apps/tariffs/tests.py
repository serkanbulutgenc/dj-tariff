# Tests for tariff models

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import BindingTariffInformation
from .models import TariffNode
from .models import validate_binding_number


class TestTariffNode:
    """Tests for the TariffNode model."""

    @pytest.mark.django_db
    def test_tariff_node_creation(self):
        """Test creating a TariffNode."""
        node = TariffNode.add_root(
            code="01",
            name="Test Section",
            node_type=TariffNode.NodeType.SECTION,
        )
        assert node.code == "01"
        assert node.name == "Test Section"
        assert node.node_type == TariffNode.NodeType.SECTION

    @pytest.mark.django_db
    def test_gtip_node_creation(self):
        """Test creating a GTIP node."""
        node = TariffNode.add_root(
            code="010121000000",
            name="Test GTIP",
            node_type=TariffNode.NodeType.GTIP,
        )
        assert node.code == "010121000000"
        assert node.node_type == TariffNode.NodeType.GTIP


class TestBindingNumberValidator:
    """Tests for the binding number format validator."""

    def test_valid_binding_numbers(self):
        """Test that valid binding numbers pass validation."""
        valid_numbers = [
            "TR340000250097",
            "TR340000250107",
            "TR330000250015",
        ]
        for number in valid_numbers:
            try:
                validate_binding_number(number)
            except ValidationError:
                pytest.fail(f"Valid binding number '{number}' raised ValidationError")

    def test_invalid_binding_number_format(self):
        """Test that invalid binding number formats fail validation."""
        invalid_numbers = [
            "BT340000250097",  # Wrong prefix
            "TR34000025009",  # Too few digits
            "TR3400002500971",  # Too many digits
            "TRA40000250097",  # Non-digit after TR
            "340000250097",  # Missing prefix
            "tr340000250097",  # Lowercase prefix
        ]
        for number in invalid_numbers:
            with pytest.raises(ValidationError):
                validate_binding_number(number)


class TestBindingTariffInformation:
    """Tests for the BindingTariffInformation model."""

    @pytest.fixture
    def gtip_node(self):
        """Create a GTIP node for testing."""
        return TariffNode.add_root(
            code="010121000000",
            name="Test GTIP Node",
            node_type=TariffNode.NodeType.GTIP,
        )

    @pytest.fixture
    def non_gtip_node(self):
        """Create a non-GTIP node for testing."""
        return TariffNode.add_root(
            code="01",
            name="Test Section Node",
            node_type=TariffNode.NodeType.SECTION,
        )

    @pytest.mark.django_db
    def test_binding_tariff_info_creation_with_gtip(self, gtip_node):
        """Test successfully creating binding tariff information with a GTIP node."""
        binding_info = BindingTariffInformation(
            tariff_node=gtip_node,
            binding_number="TR340000250097",
            valid_from=date(2026, 1, 1),
            reasoning="Test reasoning",
            description="Test description",
        )
        binding_info.save()

        assert binding_info.id is not None
        assert binding_info.binding_number == "TR340000250097"
        assert binding_info.valid_from == date(2026, 1, 1)
        assert binding_info.reasoning == "Test reasoning"
        assert binding_info.description == "Test description"

    @pytest.mark.django_db
    def test_binding_tariff_info_fails_with_non_gtip(self, non_gtip_node):
        """Test that binding tariff information raises validation error for non-GTIP nodes."""
        binding_info = BindingTariffInformation(
            tariff_node=non_gtip_node,
            binding_number="TR340000250107",
            valid_from=date(2026, 1, 1),
        )

        with pytest.raises(ValidationError) as exc_info:
            binding_info.save()

        assert "Only GTIP node types can have binding tariff information" in str(exc_info.value)

    @pytest.mark.django_db
    def test_binding_tariff_info_optional_fields(self, gtip_node):
        """Test that reasoning and description are optional fields."""
        binding_info = BindingTariffInformation(
            tariff_node=gtip_node,
            binding_number="TR330000250015",
            valid_from=date(2026, 1, 1),
            # reasoning and description are omitted
        )
        binding_info.save()

        assert binding_info.reasoning == ""
        assert binding_info.description == ""

    @pytest.mark.django_db
    def test_binding_tariff_info_unique_binding_number(self, gtip_node):
        """Test that binding_number must be unique."""
        binding_info1 = BindingTariffInformation(
            tariff_node=gtip_node,
            binding_number="TR340000250001",
            valid_from=date(2026, 1, 1),
        )
        binding_info1.save()

        # Create another GTIP node to avoid one-to-one constraint
        gtip_node2 = TariffNode.add_root(
            code="020121000000",
            name="Test GTIP Node 2",
            node_type=TariffNode.NodeType.GTIP,
        )

        binding_info2 = BindingTariffInformation(
            tariff_node=gtip_node2,
            binding_number="TR340000250001",  # Same binding number
            valid_from=date(2026, 1, 1),
        )

        with pytest.raises(Exception):  # IntegrityError on unique constraint
            binding_info2.save()

    @pytest.mark.django_db
    def test_binding_tariff_info_timestamps(self, gtip_node):
        """Test that created_at and updated_at timestamps are set correctly."""
        before_creation = timezone.now()
        binding_info = BindingTariffInformation(
            tariff_node=gtip_node,
            binding_number="TR340000250002",
            valid_from=date(2026, 1, 1),
        )
        binding_info.save()
        after_creation = timezone.now()

        assert before_creation <= binding_info.created_at <= after_creation
        assert before_creation <= binding_info.updated_at <= after_creation
        assert binding_info.created_at == binding_info.updated_at

    @pytest.mark.django_db
    def test_binding_tariff_info_updated_at_changes(self, gtip_node):
        """Test that updated_at changes when the record is updated."""
        binding_info = BindingTariffInformation(
            tariff_node=gtip_node,
            binding_number="TR340000250003",
            valid_from=date(2026, 1, 1),
            reasoning="Initial reasoning",
        )
        binding_info.save()

        original_created_at = binding_info.created_at
        original_updated_at = binding_info.updated_at

        # Wait a moment to ensure timestamp difference
        import time

        time.sleep(0.1)

        binding_info.reasoning = "Updated reasoning"
        binding_info.save()

        assert binding_info.created_at == original_created_at
        assert binding_info.updated_at > original_updated_at

    @pytest.mark.django_db
    def test_binding_tariff_info_cascade_delete(self, gtip_node):
        """Test that binding tariff information is deleted when GTIP node is deleted."""
        binding_info = BindingTariffInformation(
            tariff_node=gtip_node,
            binding_number="TR340000250004",
            valid_from=date(2026, 1, 1),
        )
        binding_info.save()
        binding_info_id = binding_info.id

        # Delete the tariff node
        gtip_node.delete()

        # Verify binding tariff information is also deleted
        assert not BindingTariffInformation.objects.filter(id=binding_info_id).exists()

    @pytest.mark.django_db
    def test_binding_tariff_info_one_to_one_relationship(self, gtip_node):
        """Test that only one binding tariff information can exist per GTIP node."""
        binding_info1 = BindingTariffInformation(
            tariff_node=gtip_node,
            binding_number="TR340000250005",
            valid_from=date(2026, 1, 1),
        )
        binding_info1.save()

        binding_info2 = BindingTariffInformation(
            tariff_node=gtip_node,
            binding_number="TR340000250006",
            valid_from=date(2026, 1, 1),
        )

        with pytest.raises(Exception):  # IntegrityError on one-to-one constraint
            binding_info2.save()

    @pytest.mark.django_db
    def test_binding_tariff_info_str_representation(self, gtip_node):
        """Test the string representation of BindingTariffInformation."""
        binding_info = BindingTariffInformation(
            tariff_node=gtip_node,
            binding_number="TR340000250007",
            valid_from=date(2026, 1, 1),
        )
        binding_info.save()

        expected_str = f"Binding {binding_info.binding_number} - {gtip_node.code}"
        assert str(binding_info) == expected_str
