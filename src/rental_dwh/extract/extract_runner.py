import argparse
import logging
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType

from rental_dwh.extract.parsers import (
    etagi_parser,
    kvartirant_parser,
    yandex_realty_parser,
)
from rental_dwh.extract.snapshot_writer import save_snapshot
from rental_dwh.utils.logging_config import setup_logging


PROJECT_ROOT = Path(
    os.environ.get(
        "RENTAL_DWH_PROJECT_ROOT",
        Path(__file__).resolve().parents[3],
    )
)


@dataclass(frozen=True)
class Source:
    parser: ModuleType
    label: str
    returns_total_count: bool = False
    request_delay: float = 0
    snapshot_format: str = "json"


SOURCES = {
    "etagi": Source(
        parser=etagi_parser,
        label="Этажи",
        returns_total_count=True,
        snapshot_format="csv",
    ),
    "kvartirant": Source(
        parser=kvartirant_parser,
        label="Квартирант",
    ),
    "yandex_realty": Source(
        parser=yandex_realty_parser,
        label="Яндекс Недвижимость",
    ),
}


def collect_apartments(source, collected_at, logger):
    apartments = []
    seen_urls = set()
    page = 1
    pages_count = None

    while pages_count is None or page <= pages_count:
        html, status_code = source.parser.get_page(page)
        parsed_page = source.parser.parse_page(html)

        if source.returns_total_count:
            page_apartments, total_count = parsed_page

            if pages_count is None:
                pages_count = (
                    math.ceil(total_count / len(page_apartments))
                    if page_apartments
                    else 0
                )
                logger.info(
                    "Всего объявлений=%s, страниц=%s",
                    total_count,
                    pages_count,
                )
        else:
            page_apartments = parsed_page

        logger.info(
            "Page %s%s: status=%s, cards=%s",
            page,
            f"/{pages_count}" if pages_count is not None else "",
            status_code,
            len(page_apartments),
        )

        if not page_apartments:
            if page == 1:
                raise ValueError(
                    f"{source.label} не вернул карточки объявлений"
                )

            break

        new_apartments_count = 0

        for apartment in page_apartments:
            apartment["collected_at"] = collected_at
            url = apartment.get("url")

            if url is None or url not in seen_urls:
                apartments.append(apartment)
                new_apartments_count += 1

            if url is not None:
                seen_urls.add(url)

        if new_apartments_count == 0:
            logger.info(
                "Страница %s не содержит новых объявлений, "
                "завершаем сбор",
                page,
            )
            break

        page += 1

        if source.request_delay and (
            pages_count is None or page <= pages_count
        ):
            time.sleep(source.request_delay)

    return apartments


def run(source_name):
    source = SOURCES[source_name]
    run_number = setup_logging(
        PROJECT_ROOT / "logs" / "extract_logs",
        source=source_name,
    )
    logger = logging.getLogger(f"{source_name}_parser")

    logger.info("Запуск сбора")

    collected_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )
    apartments = collect_apartments(source, collected_at, logger)

    logger.info("Уникальных объявлений: %s", len(apartments))

    snapshot_path = save_snapshot(
        records=apartments,
        source=source_name,
        raw_data_dir=PROJECT_ROOT / "data" / "raw",
        file_format=source.snapshot_format,
        run_number=run_number,
    )

    logger.info(
        "RAW snapshot сохранён: path=%s, records=%s",
        snapshot_path,
        len(apartments),
    )
    logger.info("Сбор завершен")
    return snapshot_path


def main():
    argument_parser = argparse.ArgumentParser(
        description="Сбор RAW-данных об аренде квартир"
    )
    argument_parser.add_argument(
        "source",
        choices=sorted(SOURCES),
        help="Источник объявлений",
    )
    arguments = argument_parser.parse_args()
    snapshot_path = run(arguments.source)
    print(snapshot_path)


if __name__ == "__main__":
    main()
