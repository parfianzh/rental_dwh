import json
from pathlib import Path
from rental_dwh.load.database import get_connection
from rental_dwh.load.repository import (
    find_existing_property_key,
    finish_etl_run,
    insert_etl_run,
    insert_listing_snapshot,
    insert_property,
    upsert_listing,
)


def read_json(file_path):
    with Path(file_path).open(encoding="utf-8") as file:
        return json.load(file)


def get_listing_identity(record):
    return (
        record["source"],
        record["source_listing_id"],
    )


PROPERTY_FIELDS = (
    "city",
    "district",
    "street",
    "house",
    "rooms",
    "floor",
)


def build_property_record(group_records):
    property_record = {}

    for field in PROPERTY_FIELDS:
        property_record[field] = next(
            (
                record[field]
                for record in group_records
                if record.get(field) is not None
            ),
            None,
        )

    return property_record


def build_property_groups(records, matched_groups):
    records_by_identity = {
        get_listing_identity(record): record
        for record in records
    }

    property_groups = []
    matched_identities = set()

    for matched_group in matched_groups:
        group_records = []

        for matched_listing in matched_group:
            identity = get_listing_identity(
                matched_listing
            )
            group_records.append(
                records_by_identity[identity]
            )
            matched_identities.add(identity)

        property_groups.append(group_records)

    for identity, record in records_by_identity.items():
        if identity not in matched_identities:
            property_groups.append([record])

    return property_groups


def run(
    processed_paths,
    matched_path,
    airflow_run_id,
    started_at,
):
    records = []

    for processed_path in processed_paths:
        records.extend(read_json(processed_path))

    matched_groups = read_json(matched_path)
    property_groups = build_property_groups(
        records,
        matched_groups,
    )

    loaded_count = 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            run_key = insert_etl_run(
                cursor=cursor,
                airflow_run_id=airflow_run_id,
                started_at=started_at,
                extracted_count=len(records),
            )

            for group_records in property_groups:
                listing_keys = {}

                for record in group_records:
                    identity = get_listing_identity(record)
                    listing_keys[identity] = upsert_listing(
                        cursor,
                        record,
                    )

                property_key = (
                    find_existing_property_key(
                        cursor,
                        list(listing_keys.values()),
                    )
                )

                if property_key is None:
                    property_record = build_property_record(
                        group_records
                    )
                    property_key = insert_property(
                        cursor,
                        property_record,
                    )

                for record in group_records:
                    identity = get_listing_identity(record)

                    insert_listing_snapshot(
                        cursor=cursor,
                        record=record,
                        listing_key=listing_keys[identity],
                        property_key=property_key,
                        run_key=run_key,
                    )
                    loaded_count += 1

            finish_etl_run(
                cursor=cursor,
                run_key=run_key,
                loaded_count=loaded_count,
            )

    return {
        "run_key": run_key,
        "extracted_count": len(records),
        "loaded_count": loaded_count,
        "property_groups_count": len(property_groups),
    }
