import json
import logging
import time
from pathlib import Path

from apps.tariffs.models import TariffNode
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import DatabaseError
from django.db import transaction
from django_elasticsearch_dsl.registries import registry

logger = logging.getLogger(__file__)


class Command(BaseCommand):
    help = (
        "Bulk seeds the database with hierarchical tariff data using django-treebeard "
        "and triggers Elasticsearch index rebuild."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/tariffs_data.json",
            help="Path to the JSON file containing hierarchical tariff data.",
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing TariffNode records before importing.",
        )
        parser.add_argument(
            "--skip-es-indexing",
            action="store_true",
            help="Skip triggering Elasticsearch reindexing after database bulk insert.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        clear_existing = options["clear"]
        skip_es = options["skip_es_indexing"]

        if not file_path.exists():
            message = f"Target data file '{file_path}' does not exist."
            logger.error(message)
            raise CommandError(message)

        self.stdout.write(
            self.style.MIGRATE_HEADING("Starting Tariff Data Seeding Process..."),
        )

        # 1. Load Data
        with file_path.open("r", encoding="utf-8") as f:
            try:
                raw_tree_data = json.load(f)
            except json.JSONDecodeError:
                logger.warning("JSON data couldn't decode")
                raise

        start_time = time.time()
        # 2. Disable Elasticsearch auto-sync during bulk processing
        registry.asynchronous = False  # Ensure sync mode if async was enabled
        # We temporarily unregister the document to prevent signal listeners from firing on save
        elasticsearch_enabled = False
        try:
            from apps.tariffs.documents import TariffNodeDocument

            registry.delete(TariffNodeDocument)

            elasticsearch_enabled = True
            self.stdout.write(self.style.WARNING("Disabled Elasticsearch auto-sync for bulk operation."))
        except ImportError, KeyError:
            self.stdout.write(
                self.style.WARNING("Elasticsearch document not registered or missing; skipping auto-sync pause.")
            )

        try:
            with transaction.atomic():
                if clear_existing:
                    self.stdout.write(
                        self.style.WARNING("Clearing existing TariffNode records..."),
                    )
                    TariffNode.objects.all().delete()

                self.stdout.write("Executing `TariffNode.load_bulk()`...")

                # treebeard load_bulk creates root nodes and child paths recursively in bulk

                TariffNode.load_bulk(
                    raw_tree_data["tariffs"],
                    parent=None,
                    batch_size=2000,
                )

                elapsed_db = time.time() - start_time
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Database seeded successfully! Created/updated root trees in {elapsed_db:.2f}s.",
                    ),
                )

        except DatabaseError as exc:
            message = f"Error during treebeard bulk seeding: {exc}"
            logging.exception(message)
            raise CommandError(message) from exc

        finally:
            # Re-register Elasticsearch document
            if elasticsearch_enabled:
                from apps.tariffs.documents import TariffNodeDocument

                registry.register_document(TariffNodeDocument)
        # 3. Optional Elasticsearch Bulk Indexing Step
        if elasticsearch_enabled and not skip_es:
            self.stdout.write(
                self.style.MIGRATE_HEADING("Rebuilding Elasticsearch index for TariffNode..."),
            )
            es_start_time = time.time()

            # Reindex via django-elasticsearch-dsl Document update
            from apps.tariffs.documents import TariffNodeDocument  # noqa

            doc = TariffNodeDocument()
            doc.get_indexing_queryset()
            doc.update(TariffNode.objects.all())

            elapsed_es = time.time() - es_start_time
            self.stdout.write(self.style.SUCCESS(f"Elasticsearch index rebuilt successfully in {elapsed_es:.2f}s."))
        total_nodes = TariffNode.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\nProcess Complete! Total Tariff Nodes in DB: {total_nodes}",
            ),
        )
