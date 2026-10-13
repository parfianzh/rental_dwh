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


def is_valid_listing(listing):
    area_sqm = listing.get("area_sqm")
    monthly_rent = listing.get("monthly_rent")

    return (
        area_sqm is not None
        and area_sqm > MIN_AREA_SQM
        and monthly_rent is not None
        and monthly_rent > MIN_MONTHLY_RENT
    )
