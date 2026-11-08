from contextlib import contextmanager

from bs4 import BeautifulSoup
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


SITE_URL = "https://realty.yandex.ru"
SEARCH_PATH = "/vladivostok/snyat/kvartira/"
SORT = "DATE_DESC"
CARD_SELECTOR = 'li[data-test="OffersSerpItem"]'
NAVIGATION_TIMEOUT_MS = 60000
CARDS_TIMEOUT_MS = 15000

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

    address_element = card.select_one(
        '[class*="AddressWithGeoLinks__addressContainer"]'
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
        attrs={"data-test": "OffersSerpItemBadge"}
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


@contextmanager
def browser_session():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            context = browser.new_context()
            page = context.new_page()
            yield page
        finally:
            browser.close()


def check_captcha(page):
    title = page.title().lower()
    url = page.url.lower()

    if "не робот" in title or "showcaptcha" in url:
        raise RuntimeError(
            "Яндекс Недвижимость вернул CAPTCHA."
        )


def get_page(page_number, browser_page):
    url = (
        f"{SITE_URL}{SEARCH_PATH}"
        f"?sort={SORT}&page={page_number}"
    )

    response = browser_page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=NAVIGATION_TIMEOUT_MS,
    )

    check_captcha(browser_page)

    if response is None or response.status != 200:
        status = response.status if response else None
        raise RuntimeError(
            f"Яндекс Недвижимость вернул HTTP {status}."
        )

    try:
        browser_page.locator(CARD_SELECTOR).first.wait_for(
            state="attached",
            timeout=CARDS_TIMEOUT_MS,
        )
    except PlaywrightTimeoutError as error:
        check_captcha(browser_page)
        raise RuntimeError(
            "Карточки Яндекс Недвижимости "
            "не появились за время ожидания."
        ) from error

    check_captcha(browser_page)

    return browser_page.content(), response.status


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
