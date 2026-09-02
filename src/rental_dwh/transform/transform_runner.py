import csv
import json
from pathlib import Path

from rental_dwh.transform.transformers.etagi_transformer import (
    transform_records as transform_etagi_records,
)
from rental_dwh.transform.transformers.kvartirant_transformer import (
    transform_records as transform_kvartirant_records,
)
from rental_dwh.transform.transformers.yandex_realty_transformer import (
    transform_records as transform_yandex_realty_records,
)
from rental_dwh.transform.matcher import (
    build_match_groups,
    find_matches,
)

def read_csv(file_path):
    with Path(file_path).open(
        encoding="utf-8",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def read_json(file_path):
    with Path(file_path).open(
        encoding="utf-8",
    ) as file:
        return json.load(file)


def write_json(records, file_path):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return file_path


def transform_etagi(raw_path, output_path):
    raw_records = read_csv(raw_path)
    transformed_records = transform_etagi_records(raw_records)
    return write_json(transformed_records, output_path)


def transform_kvartirant(raw_path, output_path):
    raw_records = read_json(raw_path)
    transformed_records = transform_kvartirant_records(raw_records)
    return write_json(transformed_records, output_path)


def transform_yandex_realty(raw_path, output_path):
    raw_records = read_json(raw_path)
    transformed_records = (
        transform_yandex_realty_records(raw_records)
    )
    return write_json(transformed_records, output_path)


TRANSFORMS = {
    "etagi": transform_etagi,
    "kvartirant": transform_kvartirant,
    "yandex_realty": transform_yandex_realty,
}


def run(source, raw_path, output_path):
    transform = TRANSFORMS[source]
    return transform(raw_path, output_path)


def match_listings(processed_paths, output_path):
    records = []

    for processed_path in processed_paths:
        records.extend(read_json(processed_path))

    matches = find_matches(records)
    groups = build_match_groups(records, matches)
    return write_json(groups, output_path)
