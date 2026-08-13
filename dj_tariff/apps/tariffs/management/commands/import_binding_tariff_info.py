import json
import logging
from datetime import datetime
from pathlib import Path

from apps.tariffs.models import BindingTariffInformation
from apps.tariffs.models import TariffNode
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Import binding tariff information from a JSON file. "
        "The JSON file should contain an array of binding tariff information objects."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            type=str,
            help="Path to the JSON file containing binding tariff information.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing BindingTariffInformation records before importing.",
        )
        parser.add_argument(
            "--skip-validation",
            action="store_true",
            help="Skip validation and attempt to import all records.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        clear_existing = options["clear"]
        skip_validation = options["skip_validation"]

        if not file_path.exists():
            message = f"Target data file '{file_path}' does not exist."
            self.stdout.write(self.style.ERROR(message))
            raise CommandError(message)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            message = f"Invalid JSON file: {e}"
            self.stdout.write(self.style.ERROR(message))
            raise CommandError(message)
        except Exception as e:
            message = f"Error reading file: {e}"
            self.stdout.write(self.style.ERROR(message))
            raise CommandError(message)

        # Ensure data is a list
        if not isinstance(data, list):
            message = "JSON file must contain an array of binding tariff information objects."
            self.stdout.write(self.style.ERROR(message))
            raise CommandError(message)

        self.stdout.write(f"Processing {len(data)} binding tariff information records...")

        if clear_existing:
            count, _ = BindingTariffInformation.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {count} existing records."))

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for index, item in enumerate(data, start=1):
                try:
                    result = self._import_binding_tariff(item, skip_validation)
                    if result == "created":
                        created_count += 1
                    elif result == "updated":
                        updated_count += 1
                    elif result == "skipped":
                        skipped_count += 1
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f"  [{index}] Error: {e}"))
                    logger.error(f"Error importing record {index}: {e}")

        # Print summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Import Summary:")
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated_count}"))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"  Skipped: {skipped_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"  Errors: {error_count}"))
        self.stdout.write("=" * 60)

        total_processed = created_count + updated_count + skipped_count + error_count
        if total_processed != len(data):
            self.stdout.write(self.style.WARNING(f"Warning: Expected {len(data)} records, processed {total_processed}"))

    def _import_binding_tariff(self, item, skip_validation=False):
        """
        Import a single binding tariff information record.

        Args:
            item: Dictionary with keys: refNo, gtip, validFrom, details (with reasoning, info)
            skip_validation: If True, skip validation checks

        Returns:
            "created", "updated", or "skipped"
        """
        # Validate required fields
        required_fields = ["refNo", "gtip", "validFrom"]
        for field in required_fields:
            if field not in item or not item[field]:
                raise ValueError(f"Missing required field: {field}")

        ref_no = item.get("refNo", "").strip()
        gtip = item.get("gtip", "").strip()
        valid_from_str = item.get("validFrom", "").strip()
        details = item.get("details", {})

        if not ref_no or not gtip or not valid_from_str:
            raise ValueError("Required fields (refNo, gtip, validFrom) cannot be empty")

        # Parse valid_from date
        try:
            # Try to parse common date formats
            for date_format in ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    valid_from = datetime.strptime(valid_from_str, date_format).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Cannot parse date '{valid_from_str}'. Expected format: YYYY-MM-DD")
        except Exception as e:
            raise ValueError(f"Invalid valid_from date: {e}")

        # Find the GTIP tariff node
        try:
            tariff_node = TariffNode.objects.get(code=gtip, node_type=TariffNode.NodeType.GTIP)
        except TariffNode.DoesNotExist:
            raise ValueError(
                f"GTIP tariff node with code '{gtip}' not found. Make sure the GTIP code exists and is of type GTIP."
            )

        # Extract reasoning and description from details
        reasoning = ""
        description = ""
        if isinstance(details, dict):
            reasoning = details.get("reasoning", "").strip()
            description = details.get("info", "").strip()

        # Create or update the binding tariff information
        binding_info, created = BindingTariffInformation.objects.update_or_create(
            tariff_node=tariff_node,
            defaults={
                "binding_number": ref_no,
                "valid_from": valid_from,
                "reasoning": reasoning,
                "description": description,
            },
        )

        action = "created" if created else "updated"
        status_text = f"Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"  {status_text}: {ref_no} (GTIP: {gtip}, Valid from: {valid_from})"))

        return action
