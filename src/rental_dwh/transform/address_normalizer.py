import re


WHITESPACE_PATTERN = re.compile(r"\s+")
HOUSE_BUILDING_SPACE_PATTERN = re.compile(
    r"\s+(?=к\S*$)",
    re.IGNORECASE,
)
RESIDENTIAL_COMPLEX_PATTERN = re.compile(
    r"^(?:жилой комплекс|жк)\b",
    re.IGNORECASE,
)
STREET_PATTERNS = (
    (
        re.compile(
            r"^(?:улица|ул\.?)\s+(?P<name>.+)$",
            re.IGNORECASE,
        ),
        "улица {name}",
    ),
    (
        re.compile(
            r"^(?P<name>.+?)\s+(?:улица|ул\.?)$",
            re.IGNORECASE,
        ),
        "улица {name}",
    ),
    (
        re.compile(
            r"^(?:проспект|пр-кт\.?)\s+(?P<name>.+)$",
            re.IGNORECASE,
        ),
        "проспект {name}",
    ),
    (
        re.compile(
            r"^(?P<name>.+?)\s+(?:проспект|пр-кт\.?)$",
            re.IGNORECASE,
        ),
        "проспект {name}",
    ),
    (
        re.compile(
            r"^(?:переулок|пер\.?)\s+(?P<name>.+)$",
            re.IGNORECASE,
        ),
        "{name} переулок",
    ),
    (
        re.compile(
            r"^(?P<name>.+?)\s+(?:переулок|пер\.?)$",
            re.IGNORECASE,
        ),
        "{name} переулок",
    ),
    (
        re.compile(
            r"^(?:бульвар)\s+(?P<name>.+)$",
            re.IGNORECASE,
        ),
        "{name} бульвар",
    ),
    (
        re.compile(
            r"^(?P<name>.+?)\s+(?:бульвар)$",
            re.IGNORECASE,
        ),
        "{name} бульвар",
    ),
    (
        re.compile(
            r"^(?:шоссе)\s+(?P<name>.+)$",
            re.IGNORECASE,
        ),
        "{name} шоссе",
    ),
    (
        re.compile(
            r"^(?P<name>.+?)\s+(?:шоссе)$",
            re.IGNORECASE,
        ),
        "{name} шоссе",
    ),
)


def normalize_text(value):
    if value is None:
        return None

    value = value.replace("ё", "е").replace("Ё", "Е")
    return WHITESPACE_PATTERN.sub(" ", value).strip()


def normalize_street(value):
    value = normalize_text(value)

    if value is None:
        return None

    if RESIDENTIAL_COMPLEX_PATTERN.match(value):
        return value

    for pattern, template in STREET_PATTERNS:
        match = pattern.match(value)

        if match:
            name = normalize_text(match.group("name"))
            return template.format(name=name)

    return f"улица {value}"


def normalize_house(value):
    value = normalize_text(value)

    if value is None:
        return None

    value = HOUSE_BUILDING_SPACE_PATTERN.sub("", value)
    return value.lower()
