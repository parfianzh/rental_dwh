import re

from rental_dwh.transform.address_normalizer import (
    normalize_house,
    normalize_street,
    normalize_text,
)
from rental_dwh.transform.transform_utils import (
    extract_listing_id,
    is_valid_listing,
    to_float,
    to_int,
    normalize_floors,
)

ROOMS_PATTERN = re.compile(r"(\d+)-к")
AREA_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*кв\.м\.")


def extract_rooms(title):
    match = ROOMS_PATTERN.search(title)

    if match:
        return int(match.group(1))

    return 0


def extract_area(title):
    match = AREA_PATTERN.search(title)

    if not match:
        return None

    area = match.group(1).replace(",", ".")
    return to_float(area)


def parse_address(address):
    city, remainder = address.split(", ", 1)
    address_parts = remainder.rsplit(", ", 2)

    if len(address_parts) == 3:
        district, street, house = address_parts
    else:
        district = None
        street, house = address_parts

    house = house.removeprefix("д.").strip()

    return {
        "city": city,
        "district": district,
        "street": street,
        "house": house,
    }


def transform_record(record):
    source_url = record.get("url")
    address = parse_address(record.get("address"))
    floor, floors_total = normalize_floors(
        record.get("floor"),
        record.get("floors"),
    )

    return {
        "source": "kvartirant",
        "source_listing_id": extract_listing_id(source_url),
        "source_url": source_url,

        "city": normalize_text(address["city"]),
        "district": normalize_text(address["district"]),
        "street": normalize_street(address["street"]),
        "house": normalize_house(address["house"]),

        "rooms": extract_rooms(record.get("title")),
        "area_sqm": extract_area(record.get("title")),
        "floor": floor,
        "floors_total": floors_total,

        "monthly_rent": to_int(record.get("price")),

        "deposit_required": None,
        "deposit_amount": None,

        "commission_required": None,
        "commission_amount": None,

        "published_date": None,
        "collected_at": record.get("collected_at"),
    }


REQUIRED_FIELDS = (
    "title",
    "address",
    "price",
    "url",
)


def is_valid_record(record):
    return all(
        record.get(field) not in (None, "")
        for field in REQUIRED_FIELDS
    )


def transform_records(records):
    transformed_records = []

    for record in records:
        if not is_valid_record(record):
            continue

        transformed_record = transform_record(record)

        if is_valid_listing(transformed_record):
            transformed_records.append(transformed_record)

    return transformed_records
