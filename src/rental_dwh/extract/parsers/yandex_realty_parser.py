import requests
from bs4 import BeautifulSoup

from rental_dwh.extract.extract_config import HEADERS, TIMEOUT


SITE_URL = "https://realty.yandex.ru"
SEARCH_PATH = "/vladivostok/snyat/kvartira/"
SORT = "DATE_DESC"


def clean_text(text):
    if text is None:
        return None

    return text.replace("\xa0", " ").strip()


def parse_card(card):
    title_element = card.find(
        attrs={"data-test": "OffersSerpItemLinkTitle"}
    )

    price_element = card.find(
        "div",
        class_="OffersSerpItem__price"
    )

    address_element = card.find(
        "div",
        class_="AddressWithGeoLinks__addressContainer--4jzfZ"
    )

    publication_date_element = card.find(
        "div",
        class_=lambda class_name: (
            class_name
            and "OffersSerpItem__publish-date" in class_name
        ),
    )

    link_element = card.find(
        "a",
        href=lambda href: href and "/offer/" in href
    )

    badges = card.find_all(
        attrs={"data-test": "Badge"}
    )

    commission = None
    deposit = None

    for badge in badges:
        badge_text = clean_text(
            badge.get_text(" ", strip=True)
        )

        if "комисси" in badge_text.lower():
            commission = badge_text

        if "залог" in badge_text.lower():
            deposit = badge_text

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
        "price": (
            clean_text(price_element.get_text(" ", strip=True))
            if price_element
            else None
        ),
        "publication_date": (
            clean_text(
                publication_date_element.get_text(" ", strip=True)
            )
            if publication_date_element
            else None
        ),
        "commission": commission,
        "deposit": deposit,
        "url": (
            f"{SITE_URL}{link_element['href']}"
            if link_element
            else None
        ),
    }


def get_page(page):
    params = {
        "sort": SORT,
        "page": page,
    }

    response = requests.get(
        f"{SITE_URL}{SEARCH_PATH}",
        params=params,
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    return response.text, response.status_code


def parse_page(html):
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    cards = soup.find_all(
        "li",
        attrs={"data-test": "OffersSerpItem"}
    )

    apartments = []

    for card in cards:
        apartments.append(
            parse_card(card)
        )

    return apartments
