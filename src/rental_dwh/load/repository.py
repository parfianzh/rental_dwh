def upsert_listing(cursor, record):
    cursor.execute(
        """
        INSERT INTO dim_listing (
            source,
            source_listing_id,
            source_url,
            area_sqm,
            floors_total,
            published_date
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (source, source_listing_id)
        DO UPDATE SET
            source_url = EXCLUDED.source_url,
            area_sqm = EXCLUDED.area_sqm,
            floors_total = COALESCE(
                EXCLUDED.floors_total,
                dim_listing.floors_total
            ),
            published_date = COALESCE(
                EXCLUDED.published_date,
                dim_listing.published_date
            )
        RETURNING listing_key
        """,
        (
            record["source"],
            record["source_listing_id"],
            record["source_url"],
            record["area_sqm"],
            record["floors_total"],
            record["published_date"],
        ),
    )

    return cursor.fetchone()[0]


def insert_property(cursor, record):
    cursor.execute(
        """
        INSERT INTO dim_property (
            city,
            district,
            street,
            house,
            rooms,
            floor
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING property_key
        """,
        (
            record["city"],
            record["district"],
            record["street"],
            record["house"],
            record["rooms"],
            record["floor"],
        ),
    )

    return cursor.fetchone()[0]


def find_existing_property_key(cursor, listing_keys):
    if not listing_keys:
        return None

    cursor.execute(
        """
        SELECT property_key
        FROM fact_listing_snapshot
        WHERE listing_key = ANY(%s)
        GROUP BY property_key
        ORDER BY
            MAX(collected_at) DESC,
            COUNT(*) DESC,
            property_key
        LIMIT 1
        """,
        (listing_keys,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return row[0]


def insert_etl_run(
    cursor,
    airflow_run_id,
    started_at,
    extracted_count,
):
    cursor.execute(
        """
        INSERT INTO etl_run (
            airflow_run_id,
            started_at,
            finished_at,
            extracted_count,
            loaded_count
        )
        VALUES (%s, %s, NULL, %s, 0)
        RETURNING run_key
        """,
        (
            airflow_run_id,
            started_at,
            extracted_count,
        ),
    )

    return cursor.fetchone()[0]


def finish_etl_run(
    cursor,
    run_key,
    loaded_count,
):
    cursor.execute(
        """
        UPDATE etl_run
        SET
            finished_at = now(),
            loaded_count = %s
        WHERE run_key = %s
        """,
        (
            loaded_count,
            run_key,
        ),
    )


def insert_listing_snapshot(
    cursor,
    record,
    listing_key,
    property_key,
    run_key,
):
    cursor.execute(
        """
        INSERT INTO fact_listing_snapshot (
            listing_key,
            property_key,
            run_key,
            collected_at,
            monthly_rent,
            deposit_required,
            deposit_amount,
            commission_required,
            commission_amount
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        """,
        (
            listing_key,
            property_key,
            run_key,
            record["collected_at"],
            record["monthly_rent"],
            record["deposit_required"],
            record["deposit_amount"],
            record["commission_required"],
            record["commission_amount"],
        ),
    )
