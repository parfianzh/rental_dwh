import logging
from datetime import date
from pathlib import Path


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_configured_run_numbers: dict[str, int] = {}


def setup_logging(
    log_dir: Path,
    source: str,
    level: int = logging.INFO,
) -> int:
    root_logger = logging.getLogger()

    if source in _configured_run_numbers:
        return _configured_run_numbers[source]

    root_logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.set_name("rental_dwh_console")
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    log_dir.mkdir(parents=True, exist_ok=True)
    current_date = date.today().isoformat()
    run_number = 1

    while True:
        suffix = "" if run_number == 1 else f"_{run_number}"
        log_file = log_dir / f"{source}_{current_date}{suffix}.log"

        if not log_file.exists():
            break

        run_number += 1

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )
    file_handler.set_name(f"{source}_file")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _configured_run_numbers[source] = run_number
    return run_number
