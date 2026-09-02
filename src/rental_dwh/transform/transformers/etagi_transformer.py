from rental_dwh.transform.address_normalizer import (
    normalize_house,
    normalize_street,
    normalize_text,
)
from rental_dwh.transform.transform_utils import (
    to_int,
    to_float,
    extract_listing_id,
)

def transform_record(record):
    deposit_amount = to_int(record.get("deposit"))
    source_url = record.get("url")

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
        "floor": to_int(record.get("floor")),
        "floors_total": to_int(record.get("floors")),

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
    return [
        transform_record(record)
        for record in records
    ]
