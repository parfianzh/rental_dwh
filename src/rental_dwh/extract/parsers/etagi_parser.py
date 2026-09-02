import json

import requests
from bs4 import BeautifulSoup

from rental_dwh.extract.extract_config import HEADERS, TIMEOUT


SITE_URL = "https://vl.etagi.com"
SEARCH_PATH = "/realty_rent/"
SORT = "datecreatedesc"


def get_page(page):
    response = requests.get(
        f"{SITE_URL}{SEARCH_PATH}",
        params={
            "orderId": SORT,
            "page": page,
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    return response.text, response.status_code


def extract_page_data(html):
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script"):
        script_text = script.string

        if not script_text or not script_text.startswith("var data="):
            continue

        page_data, _ = json.JSONDecoder().raw_decode(
            script_text[len("var data="):]
        )
        return page_data

    raise ValueError("В HTML Этажей не найден блок var data")


def parse_card(apartment):
    meta = apartment.get("meta") or {}
    object_id = apartment.get("object_id")

    return {
        "studio": apartment.get("studio"),
        "rooms": apartment.get("rooms"),
        "square": apartment.get("square"),
        "floor": apartment.get("floor"),
        "floors": apartment.get("floors"),
        "city": meta.get("city"),
        "street": meta.get("street"),
        "house_address_number": apartment.get("house_address_number"),
        "price": apartment.get("price"),
        "deposit": apartment.get("deposit"),
        "url": (
            f"{SITE_URL}/realty_rent/{object_id}/"
            if object_id is not None
            else None
        ),
    }


def parse_page(html):
    page_data = extract_page_data(html)
    apartments = [
        parse_card(apartment)
        for apartment in page_data["lists"]["rents"]
    ]
    total_count = page_data["filters"]["rents"]["count"]

    return apartments, total_count
