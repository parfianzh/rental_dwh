from itertools import combinations

MAX_AREA_DIFFERENCE = 2.0
MAX_PRICE_DIFFERENCE_PERCENT = 7.0

EQUAL_FIELDS = (
    "city",
    "street",
    "house",
    "rooms",
    "floor",
)


def calculate_price_difference_percent(
    left_price,
    right_price,
):
    if left_price is None or right_price is None:
        return None

    highest_price = max(left_price, right_price)

    if highest_price == 0:
        return 0.0

    return (
        abs(left_price - right_price)
        / highest_price
        * 100
    )


def listings_match(left, right):
    if left["source"] == right["source"]:
        return False

    for field in EQUAL_FIELDS:
        if left.get(field) != right.get(field):
            return False

    left_area = left.get("area_sqm")
    right_area = right.get("area_sqm")

    if left_area is None or right_area is None:
        return False

    if abs(left_area - right_area) > MAX_AREA_DIFFERENCE:
        return False

    price_difference = calculate_price_difference_percent(
        left.get("monthly_rent"),
        right.get("monthly_rent"),
    )

    if price_difference is None:
        return False

    return price_difference <= MAX_PRICE_DIFFERENCE_PERCENT


def create_match_record(left, right):
    price_difference = calculate_price_difference_percent(
        left["monthly_rent"],
        right["monthly_rent"],
    )

    return {
        "left_source": left["source"],
        "left_source_listing_id": left[
            "source_listing_id"
        ],
        "left_source_url": left["source_url"],

        "right_source": right["source"],
        "right_source_listing_id": right[
            "source_listing_id"
        ],
        "right_source_url": right["source_url"],

        "match_method": (
            "address_rooms_floor_area_price"
        ),
        "area_difference": round(
            abs(left["area_sqm"] - right["area_sqm"]),
            2,
        ),
        "price_difference_percent": round(
            price_difference,
            2,
        ),
    }


def find_matches(records):
    matches = []

    for left, right in combinations(records, 2):
        if listings_match(left, right):
            matches.append(
                create_match_record(left, right)
            )

    return matches


def build_match_groups(records, matches):
    listings = {
        (
            record["source"],
            record["source_listing_id"],
        ): {
            "source": record["source"],
            "source_listing_id": record[
                "source_listing_id"
            ],
            "source_url": record["source_url"],
        }
        for record in records
    }
    connections = {}

    for match in matches:
        left_key = (
            match["left_source"],
            match["left_source_listing_id"],
        )
        right_key = (
            match["right_source"],
            match["right_source_listing_id"],
        )

        connections.setdefault(left_key, set()).add(
            right_key
        )
        connections.setdefault(right_key, set()).add(
            left_key
        )

    groups = []
    visited = set()

    for listing_key in sorted(connections):
        if listing_key in visited:
            continue

        group_keys = []
        pending = [listing_key]

        while pending:
            current_key = pending.pop()

            if current_key in visited:
                continue

            visited.add(current_key)
            group_keys.append(current_key)
            pending.extend(
                connections[current_key] - visited
            )

        groups.append(
            [
                listings[key]
                for key in sorted(group_keys)
            ]
        )

    return groups
