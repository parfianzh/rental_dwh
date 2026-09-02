import re
from datetime import date, datetime, timedelta

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


AREA_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*м²")
ROOMS_PATTERN = re.compile(r"(\d+)-комнатная квартира")
FLOORS_PATTERN = re.compile(r"(\d+)\s*этаж из\s*(\d+)")
PRICE_PATTERN = re.compile(r"(\d[\d\s]*)\s*₽")
COMMISSION_PATTERN = re.compile(r"комиссия\s*(\d+)%")
MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def parse_title(title):
    area_match = AREA_PATTERN.search(title)
    rooms_match = ROOMS_PATTERN.search(title)
    floors_match = FLOORS_PATTERN.search(title)

    area = None

    if area_match:
        area = to_float(
            area_match.group(1).replace(",", ".")
        )

    if "квартира-студия" in title:
        rooms = 0
    elif rooms_match:
        rooms = to_int(rooms_match.group(1))
    else:
        rooms = None

    floor = None
    floors_total = None

    if floors_match:
        floor = to_int(floors_match.group(1))
        floors_total = to_int(floors_match.group(2))

    return {
        "rooms": rooms,
        "area_sqm": area,
        "floor": floor,
        "floors_total": floors_total,
    }


def extract_monthly_rent(price):
    match = PRICE_PATTERN.search(price)

    if not match:
        return None

    amount = match.group(1).replace(" ", "")
    return to_int(amount)


def parse_commission(commission, monthly_rent):
    if commission is None:
        return {
            "commission_required": None,
            "commission_amount": None,
        }

    if commission == "без комиссии":
        return {
            "commission_required": False,
            "commission_amount": 0,
        }

    match = COMMISSION_PATTERN.search(commission)

    if not match or monthly_rent is None:
        return {
            "commission_required": True,
            "commission_amount": None,
        }

    commission_percent = to_int(match.group(1))
    commission_amount = round(
        monthly_rent * commission_percent / 100
    )

    return {
        "commission_required": True,
        "commission_amount": commission_amount,
    }


def parse_deposit(deposit):
    if deposit is None:
        return {
            "deposit_required": None,
            "deposit_amount": None,
        }

    if deposit == "без залога":
        return {
            "deposit_required": False,
            "deposit_amount": 0,
        }

    return {
        "deposit_required": True,
        "deposit_amount": None,
    }


def parse_address(address):
    parts = [
        part.strip()
        for part in address.split(",")
    ]

    if len(parts) == 3:
        city = parts.pop(0)
    else:
        city = "Владивосток"

    street, house = parts

    return {
        "city": city,
        "district": None,
        "street": street,
        "house": house,
    }


def parse_publication_date(publication_date, collected_at):
    collected_datetime = datetime.fromisoformat(collected_at)

    if publication_date == "сегодня":
        return collected_datetime.date().isoformat()

    if publication_date == "вчера":
        return (
            collected_datetime.date() - timedelta(days=1)
        ).isoformat()

    relative_date_match = re.fullmatch(
        r"(\d+)\s+"
        r"(секунд(?:у|ы)?|минут(?:у|ы)?|"
        r"час(?:а|ов)?|д(?:ень|ня|ней)) назад",
        publication_date.casefold(),
    )

    if relative_date_match:
        amount = to_int(relative_date_match.group(1))
        unit = relative_date_match.group(2)

        if unit.startswith("секунд"):
            delta = timedelta(seconds=amount)
        elif unit.startswith("минут"):
            delta = timedelta(minutes=amount)
        elif unit.startswith("час"):
            delta = timedelta(hours=amount)
        else:
            delta = timedelta(days=amount)

        published_datetime = (
            collected_datetime - delta
        )
        return published_datetime.date().isoformat()

    day, month_name, year = publication_date.split()

    return date(
        year=to_int(year),
        month=MONTHS[month_name],
        day=to_int(day),
    ).isoformat()


def transform_record(record):
    source_url = record.get("url")
    title = parse_title(record.get("title"))
    address = parse_address(record.get("address"))
    monthly_rent = extract_monthly_rent(
        record.get("price")
    )
    commission = parse_commission(
        record.get("commission"),
        monthly_rent,
    )
    deposit = parse_deposit(record.get("deposit"))

    return {
        "source": "yandex_realty",
        "source_listing_id": extract_listing_id(source_url),
        "source_url": source_url,

        "city": normalize_text(address["city"]),
        "district": normalize_text(address["district"]),
        "street": normalize_street(address["street"]),
        "house": normalize_house(address["house"]),

        "rooms": title["rooms"],
        "area_sqm": title["area_sqm"],
        "floor": title["floor"],
        "floors_total": title["floors_total"],

        "monthly_rent": monthly_rent,

        "deposit_required": deposit["deposit_required"],
        "deposit_amount": deposit["deposit_amount"],

        "commission_required": commission[
            "commission_required"
        ],
        "commission_amount": commission[
            "commission_amount"
        ],

        "published_date": parse_publication_date(
            record.get("publication_date"),
            record.get("collected_at"),
        ),
        "collected_at": record.get("collected_at"),
    }


def transform_records(records):
    return [
        transform_record(record)
        for record in records
    ]
