import os

import psycopg


def get_connection():
    return psycopg.connect(
        host=os.environ.get(
            "DWH_DB_HOST",
            "localhost",
        ),
        port=os.environ.get(
            "DWH_DB_PORT",
            "5433",
        ),
        dbname=os.environ.get(
            "DWH_DB_NAME",
            "rental_dwh",
        ),
        user=os.environ.get(
            "DWH_DB_USER",
            "rental",
        ),
        password=os.environ.get(
            "DWH_DB_PASSWORD",
            "rental",
        ),
    )