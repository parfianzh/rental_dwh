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