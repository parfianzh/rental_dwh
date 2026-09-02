import re

from rental_dwh.transform.address_normalizer import (
    normalize_house,
    normalize_street,
    normalize_text,
)
from rental_dwh.transform.transform_utils import (
    extract_listing_id,
    to_float,
    to_int,
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
    district, street, house = remainder.rsplit(", ", 2)

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
        "floor": to_int(record.get("floor")),
        "floors_total": to_int(record.get("floors")),

        "monthly_rent": to_int(record.get("price")),

        "deposit_required": None,
        "deposit_amount": None,

        "commission_required": None,
        "commission_amount": None,

        "published_date": None,
        "collected_at": record.get("collected_at"),
    }


def transform_records(records):
    return [
        transform_record(record)
        for record in records
    ]
