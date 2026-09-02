CREATE SCHEMA IF NOT EXISTS marts;


CREATE OR REPLACE VIEW marts.market_daily AS
WITH property_daily AS (
    SELECT
        (
            s.collected_at
            AT TIME ZONE 'Europe/Moscow'
        )::date AS snapshot_date,
        s.property_key,
        p.city,
        p.rooms,
        AVG(s.monthly_rent) AS monthly_rent,
        AVG(l.area_sqm) AS area_sqm,
        COUNT(DISTINCT s.listing_key) AS listing_count
    FROM fact_listing_snapshot AS s
    JOIN dim_property AS p
        ON p.property_key = s.property_key
    JOIN dim_listing AS l
        ON l.listing_key = s.listing_key
    GROUP BY
        snapshot_date,
        s.property_key,
        p.city,
        p.rooms
)
SELECT
    snapshot_date,
    city,
    rooms,

    COUNT(*) AS property_count,
    SUM(listing_count) AS listing_count,

    ROUND(AVG(monthly_rent))::integer
        AS avg_monthly_rent,

    PERCENTILE_CONT(0.5)
        WITHIN GROUP (ORDER BY monthly_rent)::integer
        AS median_monthly_rent,

    MIN(monthly_rent)::integer
        AS min_monthly_rent,

    MAX(monthly_rent)::integer
        AS max_monthly_rent,

    ROUND(
        AVG(monthly_rent / NULLIF(area_sqm, 0))
    )::integer AS avg_rent_per_sqm

FROM property_daily
GROUP BY
    snapshot_date,
    city,
    rooms;


CREATE OR REPLACE VIEW marts.source_daily AS
WITH listing_first_seen AS (
    SELECT
        listing_key,
        MIN(
            (
                collected_at
                AT TIME ZONE 'Europe/Moscow'
            )::date
        ) AS first_seen_date
    FROM fact_listing_snapshot
    GROUP BY listing_key
)
SELECT
    (
        s.collected_at
        AT TIME ZONE 'Europe/Moscow'
    )::date AS snapshot_date,

    l.source,

    COUNT(DISTINCT s.listing_key)
        AS listing_count,

    COUNT(DISTINCT s.property_key)
        AS property_count,

    COUNT(
        DISTINCT s.listing_key
    ) FILTER (
        WHERE f.first_seen_date = (
            s.collected_at
            AT TIME ZONE 'Europe/Moscow'
        )::date
    ) AS new_listing_count,

    ROUND(AVG(s.monthly_rent))::integer
        AS avg_monthly_rent,

    PERCENTILE_CONT(0.5)
        WITHIN GROUP (ORDER BY s.monthly_rent)::integer
        AS median_monthly_rent,

    MIN(s.monthly_rent)
        AS min_monthly_rent,

    MAX(s.monthly_rent)
        AS max_monthly_rent,

    p.city

FROM fact_listing_snapshot AS s
JOIN dim_listing AS l
    ON l.listing_key = s.listing_key
JOIN dim_property AS p
    ON p.property_key = s.property_key
JOIN listing_first_seen AS f
    ON f.listing_key = s.listing_key
GROUP BY
    snapshot_date,
    l.source,
    p.city;


CREATE OR REPLACE VIEW marts.listing_lifecycle AS
WITH history AS (
    SELECT
        s.*,
        (
            s.collected_at
            AT TIME ZONE 'Europe/Moscow'
        )::date AS snapshot_date
    FROM fact_listing_snapshot AS s
),

listing_stats AS (
    SELECT
        listing_key,

        MIN(snapshot_date) AS first_seen_date,
        MAX(snapshot_date) AS last_seen_date,

        COUNT(DISTINCT snapshot_date)
            AS observation_count,

        MAX(snapshot_date) - MIN(snapshot_date) + 1
            AS observed_lifetime_days,

        (ARRAY_AGG(
            monthly_rent
            ORDER BY collected_at, snapshot_key
        ))[1] AS first_monthly_rent,

        (ARRAY_AGG(
            monthly_rent
            ORDER BY collected_at DESC, snapshot_key DESC
        ))[1] AS last_monthly_rent,

        MIN(monthly_rent) AS min_monthly_rent,
        MAX(monthly_rent) AS max_monthly_rent,

        COUNT(DISTINCT monthly_rent) - 1
            AS price_change_count

    FROM history
    GROUP BY listing_key
),

latest_property AS (
    SELECT DISTINCT ON (listing_key)
        listing_key,
        property_key
    FROM history
    ORDER BY
        listing_key,
        collected_at DESC,
        snapshot_key DESC
),

latest_snapshot_date AS (
    SELECT MAX(snapshot_date) AS snapshot_date
    FROM history
)

SELECT
    s.listing_key,
    l.source,
    l.source_listing_id,
    l.source_url,

    p.property_key,
    p.city,
    p.district,
    p.street,
    p.house,
    p.rooms,
    p.floor,

    l.area_sqm,
    l.floors_total,
    l.published_date,

    s.first_seen_date,
    s.last_seen_date,
    s.observation_count,
    s.observed_lifetime_days,

    s.first_monthly_rent,
    s.last_monthly_rent,
    s.min_monthly_rent,
    s.max_monthly_rent,
    s.price_change_count,

    s.last_monthly_rent
        - s.first_monthly_rent
        AS price_change_amount,

    ROUND(
        100.0
        * (
            s.last_monthly_rent
            - s.first_monthly_rent
        )
        / NULLIF(s.first_monthly_rent, 0),
        2
    ) AS price_change_percent,

    s.last_seen_date = d.snapshot_date
        AS is_active_on_latest_snapshot

FROM listing_stats AS s
JOIN dim_listing AS l
    ON l.listing_key = s.listing_key
JOIN latest_property AS lp
    ON lp.listing_key = s.listing_key
JOIN dim_property AS p
    ON p.property_key = lp.property_key
CROSS JOIN latest_snapshot_date AS d;


CREATE OR REPLACE VIEW marts.cross_source_properties AS
SELECT
    property_key,
    city,
    district,
    street,
    house,
    rooms,
    floor,

    COUNT(DISTINCT source) AS source_count,

    MIN(first_seen_date) AS first_seen_date,
    MAX(last_seen_date) AS last_seen_date,

    MAX(last_monthly_rent) FILTER (
        WHERE source = 'etagi'
    ) AS etagi_monthly_rent,

    MAX(source_url) FILTER (
        WHERE source = 'etagi'
    ) AS etagi_url,

    MAX(last_monthly_rent) FILTER (
        WHERE source = 'kvartirant'
    ) AS kvartirant_monthly_rent,

    MAX(source_url) FILTER (
        WHERE source = 'kvartirant'
    ) AS kvartirant_url,

    MAX(last_monthly_rent) FILTER (
        WHERE source = 'yandex_realty'
    ) AS yandex_monthly_rent,

    MAX(source_url) FILTER (
        WHERE source = 'yandex_realty'
    ) AS yandex_url,

    MAX(last_monthly_rent)
        - MIN(last_monthly_rent)
        AS price_difference_amount,

    ROUND(
        100.0
        * (
            MAX(last_monthly_rent)
            - MIN(last_monthly_rent)
        )
        / NULLIF(MAX(last_monthly_rent), 0),
        2
    ) AS price_difference_percent

FROM marts.listing_lifecycle
WHERE is_active_on_latest_snapshot
GROUP BY
    property_key,
    city,
    district,
    street,
    house,
    rooms,
    floor
HAVING COUNT(DISTINCT source) > 1;