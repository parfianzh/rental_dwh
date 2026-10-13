def to_int(value):
    if value in (None, ""):
        return None

    return int(value)


def to_float(value):
    if value in (None, ""):
        return None

    return float(value)


def extract_listing_id(url):
    if not url:
        return None

    return url.rstrip("/").split("/")[-1]


MIN_AREA_SQM = 5
MIN_MONTHLY_RENT = 7000
MAX_FLOOR = 44


def normalize_floors(floor, floors_total):
    floor = to_int(floor)
    floors_total = to_int(floors_total)

    if (
        floor is not None
        and floors_total is not None
        and floor > floors_total
    ):
        floor, floors_total = floors_total, floor

    if floor is not None and floor > MAX_FLOOR:
        floor = None

    if floors_total is not None and floors_total > MAX_FLOOR:
        floors_total = None

    return floor, floors_total


def is_valid_listing(listing):
    area_sqm = listing.get("area_sqm")
    monthly_rent = listing.get("monthly_rent")

    return (
        area_sqm is not None
        and area_sqm > MIN_AREA_SQM
        and monthly_rent is not None
        and monthly_rent > MIN_MONTHLY_RENT
    )
