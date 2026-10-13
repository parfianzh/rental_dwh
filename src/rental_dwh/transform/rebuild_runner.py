import csv
import json
from datetime import datetime
from pathlib import Path

from rental_dwh.transform.transform_runner import (
    match_listings,
    run as run_transform,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]

SOURCES = {
    "etagi": ".csv",
    "kvartirant": ".json",
    "yandex_realty": ".json",
}


def read_first_record(file_path):
    if file_path.suffix == ".csv":
        with file_path.open(
            encoding="utf-8",
            newline="",
        ) as file:
            return next(csv.DictReader(file), None)

    with file_path.open(encoding="utf-8") as file:
        records = json.load(file)

    return records[0] if records else None


def get_collected_at(file_path):
    first_record = read_first_record(file_path)

    if first_record is None:
        raise ValueError(f"Пустой RAW-файл: {file_path}")

    collected_at = first_record.get("collected_at")

    if not collected_at:
        raise ValueError(
            f"В RAW-файле отсутствует collected_at: {file_path}"
        )

    return datetime.fromisoformat(collected_at)


def select_latest_snapshots(raw_source_dir, file_suffix):
    snapshots = {}

    for file_path in raw_source_dir.glob(
        f"*{file_suffix}"
    ):
        collected_at = get_collected_at(file_path)
        snapshot_date = collected_at.date().isoformat()
        current_snapshot = snapshots.get(snapshot_date)

        if (
            current_snapshot is None
            or collected_at > current_snapshot[0]
        ):
            snapshots[snapshot_date] = (
                collected_at,
                file_path,
            )

    return {
        snapshot_date: file_path
        for snapshot_date, (_, file_path)
        in snapshots.items()
    }


def run():
    raw_data_dir = PROJECT_ROOT / "data" / "raw"
    processed_data_dir = (
        PROJECT_ROOT / "data" / "processed"
    )

    snapshots = {
        source: select_latest_snapshots(
            raw_data_dir / source,
            file_suffix,
        )
        for source, file_suffix in SOURCES.items()
    }

    complete_dates = sorted(
        set.intersection(
            *(
                set(source_snapshots)
                for source_snapshots in snapshots.values()
            )
        )
    )

    for snapshot_date in complete_dates:
        processed_paths = []

        for source in SOURCES:
            raw_path = snapshots[source][snapshot_date]
            processed_path = (
                processed_data_dir
                / source
                / f"{snapshot_date}.json"
            )

            run_transform(
                source,
                raw_path,
                processed_path,
            )
            processed_paths.append(processed_path)

        matched_path = (
            processed_data_dir
            / "matched"
            / f"{snapshot_date}.json"
        )

        match_listings(
            processed_paths,
            matched_path,
        )

        print(
            f"{snapshot_date}: Transform и Match завершены"
        )

    print(
        f"Пересобрано полных дневных снимков: "
        f"{len(complete_dates)}"
    )

    return complete_dates