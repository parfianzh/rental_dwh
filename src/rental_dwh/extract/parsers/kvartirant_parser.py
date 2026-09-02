import requests
from bs4 import BeautifulSoup

from rental_dwh.extract.extract_config import HEADERS, TIMEOUT


SITE_URL = "https://kvartirant.plus" 
SEARCH_PATH = "/predlozhenija/snyat/kvartiry/"
SORT = "DATE_CREATE"
SORT_ORDER = "DESC"


def clean_text(text):
    if text is None:
        return None

    return text.replace("\xa0", " ").strip()


def get_property_value(card, property_name):
    for property_element in card.select(".catalog-card__property"):
        name_element = property_element.select_one(
            ".catalog-card__property-name"
        )

        if not name_element:
            continue

        name = clean_text(name_element.get_text(" ", strip=True))

        if name.rstrip(":") != property_name:
            continue

        value_element = property_element.select_one(
            ".catalog-card__property-value"
        )
        return (
            clean_text(value_element.get_text(" ", strip=True))
            if value_element
            else None
        )

    return None


def get_page(page):
    response = requests.get(
        f"{SITE_URL}{SEARCH_PATH}",
        params={
            "sort": SORT,
            "order": SORT_ORDER,
            "PAGEN_1": page,
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    return response.text, response.status_code


def parse_card(card):
    title_element = card.select_one(".catalog-card__name")
    address_element = card.select_one(".map-link__address")
    price_element = card.select_one(
        ".catalog-card__price [data-currency-base]"
    )
    link_element = card.select_one(".catalog-card__name[href]")
    floor, separator, floors = (
        get_property_value(card, "Этаж") or ""
    ).partition("/")

    return {
        "title": (
            clean_text(title_element.get_text(" ", strip=True))
            if title_element
            else None
        ),
        "address": (
            clean_text(address_element.get_text(" ", strip=True))
            if address_element
            else None
        ),
        "floor": floor or None,
        "floors": floors or None if separator else None,
        "price": (
            price_element.get("data-currency-base")
            if price_element
            else None
        ),
        "url": (
            SITE_URL + link_element["href"]
            if link_element
            else None
        ),
    }


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")

    return [
        parse_card(card)
        for card in soup.select(".catalog-card")
    ]
