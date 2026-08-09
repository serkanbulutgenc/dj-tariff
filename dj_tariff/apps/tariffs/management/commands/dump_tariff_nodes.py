import json
from pathlib import Path

from apps.tariffs.models import TariffNode
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError


class Command(BaseCommand):
    help = "Dump all `TariffNode` records to a JSON file under the `data/` folder by default."

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            nargs="?",
            type=str,
            default="data/tariffs_data.json",
            help="Optional output file path (default: data/tariffs_data.json)",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])

        # Ensure target directory exists
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise CommandError(f"Unable to create target directory: {e}")
        from datetime import datetime

        # Add UTC timestamp to filename for basic versioning
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        if file_path.suffix:
            out_file = file_path.with_name(f"{file_path.stem}-{ts}{file_path.suffix}")
        else:
            out_file = file_path.with_name(f"{file_path.name}-{ts}")

        # Ensure target directory exists
        try:
            out_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise CommandError(f"Unable to create target directory: {e}")

        # Prefer treebeard's dump_bulk if available to produce the nested format
        try:
            if hasattr(TariffNode, "dump_bulk"):
                try:
                    dumped = TariffNode.dump_bulk()
                except TypeError:
                    # Some treebeard versions accept root nodes as an argument
                    roots = list(TariffNode.get_root_nodes())
                    dumped = TariffNode.dump_bulk(roots)
                output = {"tariffs": dumped}
            else:
                # Fallback: build nested structure compatible with load_bulk
                def node_to_dict(node):
                    data = {
                        "code": node.code,
                        "name": node.name,
                        "node_type": node.node_type,
                        "description_detail": None,
                    }
                    children = [
                        node_to_dict(c) for c in node.get_children().order_by("code")
                    ]
                    return {"data": data, "children": children}

                roots = TariffNode.get_root_nodes().order_by("code")
                dumped = [node_to_dict(r) for r in roots]
                output = {"tariffs": dumped}

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

        except Exception as e:
            raise CommandError(f"Failed to dump TariffNode data: {e}")

        # Count total nodes for reporting
        total = TariffNode.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"Wrote {total} TariffNode(s) to {out_file}"),
        )
