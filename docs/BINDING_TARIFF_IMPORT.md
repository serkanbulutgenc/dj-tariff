# Binding Tariff Information Import Management Command

## Overview

The `import_binding_tariff_info` management command allows you to bulk import binding tariff information from a JSON file into the database.

## Usage

### Basic Usage

```bash
python manage.py import_binding_tariff_info <path_to_json_file>
```

Example:
```bash
python manage.py import_binding_tariff_info data/binding_tariffs_example.json
```

### Command Options

#### `--clear`
Clear existing BindingTariffInformation records before importing.

```bash
python manage.py import_binding_tariff_info data/binding_tariffs.json --clear
```

#### `--skip-validation`
Skip validation checks and attempt to import all records (not recommended).

```bash
python manage.py import_binding_tariff_info data/binding_tariffs.json --skip-validation
```

## JSON File Format

The JSON file must contain an array of binding tariff information objects. Each object should have the following structure:

```json
[
  {
    "refNo": "TR340000250097",
    "gtip": "010121000000",
    "validFrom": "2026-01-01",
    "details": {
      "reasoning": "Optional reasoning text",
      "info": "Optional description text"
    }
  }
]
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refNo` | string | Yes | Binding number in format: TR + 12 digits (e.g., TR340000250097) |
| `gtip` | string | Yes | GTIP code that already exists in the database (12 digits) |
| `validFrom` | string | Yes | Date when the binding becomes valid (supported formats: YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY, YYYY/MM/DD) |
| `details.reasoning` | string | No | Reasoning for the binding tariff information |
| `details.info` | string | No | Description text for the binding tariff information |

## Data Mapping

The command maps JSON fields to model fields as follows:

| JSON Field | Model Field |
|------------|------------|
| `refNo` | `binding_number` |
| `gtip` | `tariff_node` (looks up TariffNode by code and GTIP type) |
| `validFrom` | `valid_from` |
| `details.reasoning` | `reasoning` |
| `details.info` | `description` |

## Import Summary

After import completion, the command displays a summary showing:
- Number of records created
- Number of records updated (if binding number already exists for a GTIP)
- Number of records skipped
- Number of errors encountered

Example output:
```
============================================================
Import Summary:
  Created: 15
  Updated: 2
  Skipped: 0
  Errors: 0
============================================================
```

## Error Handling

The command validates:
1. **Required fields**: refNo, gtip, validFrom must be present and non-empty
2. **Binding number format**: Must match pattern TR + 12 digits
3. **GTIP existence**: The GTIP code must exist in the database as a GTIP-type TariffNode
4. **Date format**: Valid date in one of the supported formats

Errors are logged and reported in the import summary. The command uses database transactions to ensure atomicity - all records are imported or all are rolled back if an error occurs.

## Example JSON File

See [binding_tariffs_example.json](binding_tariffs_example.json) for an example of a correctly formatted JSON file.

## Notes

- The command uses no external dependencies beyond Django
- Records are processed in a single database transaction for data consistency
- If a binding tariff information record already exists for a GTIP node, it will be updated with the new values
- All timestamps (created_at, updated_at) are managed automatically by Django
