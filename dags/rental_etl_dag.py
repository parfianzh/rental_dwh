from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from airflow.sdk import DAG, get_current_context, task

from rental_dwh.extract.extract_runner import run as run_extract
from rental_dwh.transform.transform_runner import (
    match_listings as run_match_listings,
    run as run_transform,
)
from rental_dwh.load.load_runner import run as run_load


SOURCES = (
    "etagi",
    "kvartirant",
    "yandex_realty",
)


@task
def extract(source):
    return str(run_extract(source))


@task
def transform(source, raw_path):
    raw_path = Path(raw_path)
    output_path = (
        raw_path.parents[2]
        / "processed"
        / source
        / raw_path.with_suffix(".json").name
    )

    return str(run_transform(source, raw_path, output_path))


@task
def match_listings(processed_paths):
    first_processed_path = Path(processed_paths[0])
    output_path = (
        first_processed_path.parents[1]
        / "matched"
        / first_processed_path.name
    )

    return str(
        run_match_listings(processed_paths, output_path)
    )


@task
def load_dwh(processed_paths, matched_path):
    context = get_current_context()
    dag_run = context["dag_run"]

    return run_load(
        processed_paths=processed_paths,
        matched_path=matched_path,
        airflow_run_id=dag_run.run_id,
        started_at=dag_run.start_date,
    )


with DAG(
    dag_id="rental_etl",
    start_date=datetime(
        2026,
        8,
        26,
        tzinfo=ZoneInfo("Europe/Moscow"),
    ),
    schedule="0 15 * * *",
    catchup=False,
    tags=["rental", "etl"],
) as dag:
    processed_paths = []

    for source in SOURCES:
        raw_path = extract.override(
            task_id=f"extract_{source}"
        )(source)

        processed_path = transform.override(
            task_id=f"transform_{source}"
        )(source, raw_path)

        processed_paths.append(processed_path)

    matched_path = match_listings(processed_paths)

    load_dwh(
        processed_paths,
        matched_path,
    )
