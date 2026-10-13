from rental_dwh.transform.address_normalizer import (
    normalize_house,
    normalize_street,
    normalize_text,
)
from rental_dwh.transform.transform_utils import (
    to_int,
    to_float,
    extract_listing_id,
    is_valid_listing,
    normalize_floors,
)

def transform_record(record):
    deposit_amount = to_int(record.get("deposit"))
    source_url = record.get("url")
    floor, floors_total = normalize_floors(
        record.get("floor"),
        record.get("floors"),
    )

    return {
        "source": "etagi",
        "source_listing_id": extract_listing_id(source_url),
        "source_url": source_url,

        "city": normalize_text(record.get("city")),
        "district": None,
        "street": normalize_street(record.get("street")),
        "house": normalize_house(
            record.get("house_address_number")
        ),

        "rooms": to_int(record.get("rooms")),
        "area_sqm": to_float(record.get("square")),
        "floor": floor,
        "floors_total": floors_total,

        "monthly_rent": to_int(record.get("price")),

        "deposit_required": (
            deposit_amount > 0
            if deposit_amount is not None
            else None
        ),
        "deposit_amount": deposit_amount,

        "commission_required": None,
        "commission_amount": None,

        "published_date": None,
        "collected_at": record.get("collected_at"),
    }
    
    
def transform_records(records):
    transformed_records = []

    for record in records:
        transformed_record = transform_record(record)

        if is_valid_listing(transformed_record):
            transformed_records.append(transformed_record)

    return transformed_records
