import csv
import json
from datetime import date
from pathlib import Path


SUPPORTED_FORMATS = {"csv", "json"}


def _write_csv(file, records):
    fieldnames = list(
        dict.fromkeys(
            field
            for record in records
            for field in record
        )
    )
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)


def _write_json(file, records):
    json.dump(records, file, ensure_ascii=False, indent=2)


def save_snapshot(
    records: list[dict],
    source: str,
    raw_data_dir: Path,
    file_format: str = "json",
    snapshot_date: date | None = None,
    run_number: int = 1,
) -> Path:
    if file_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported snapshot format: {file_format}")

    snapshot_date = snapshot_date or date.today()
    source_dir = raw_data_dir / source
    source_dir.mkdir(parents=True, exist_ok=True)

    suffix = "" if run_number == 1 else f"_{run_number}"
    snapshot_path = source_dir / (
        f"{snapshot_date.isoformat()}{suffix}.{file_format}"
    )
    temporary_path = snapshot_path.with_suffix(
        f".{file_format}.tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
        newline="" if file_format == "csv" else None,
    ) as file:
        if file_format == "csv":
            _write_csv(file, records)
        else:
            _write_json(file, records)

    temporary_path.replace(snapshot_path)

    return snapshot_path