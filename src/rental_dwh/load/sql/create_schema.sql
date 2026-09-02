CREATE TYPE listing_source AS ENUM (
    'etagi',
    'kvartirant',
    'yandex_realty'
);


CREATE TABLE dim_property (
    property_key bigint GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    city varchar(100) NOT NULL,
    district varchar(150),
    street varchar(200),
    house varchar(50),

    rooms smallint,
    floor smallint
);

CREATE TABLE dim_listing (
    listing_key bigint GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    
    source listing_source NOT NULL,
    source_listing_id varchar(100) NOT NULL,
    source_url text NOT NULL,

    area_sqm numeric(7, 2) NOT NULL,
    floors_total smallint,
    
    published_date date,

    CONSTRAINT uq_dim_listing_source_id
        UNIQUE (source, source_listing_id)
);

CREATE TABLE etl_run (
    run_key bigint GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    airflow_run_id varchar(250) NOT NULL,
    started_at timestamptz NOT NULL,
    finished_at timestamptz,

    extracted_count integer NOT NULL,
    loaded_count integer NOT NULL,

    CONSTRAINT uq_etl_run_airflow_run_id
        UNIQUE (airflow_run_id)
);

CREATE TABLE fact_listing_snapshot (
    snapshot_key bigint GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    listing_key bigint NOT NULL,
    property_key bigint NOT NULL,
    run_key bigint NOT NULL,

    collected_at timestamptz NOT NULL,

    monthly_rent integer NOT NULL,

    deposit_required boolean,
    deposit_amount integer,

    commission_required boolean,
    commission_amount integer,

    CONSTRAINT fk_snapshot_listing
        FOREIGN KEY (listing_key)
        REFERENCES dim_listing (listing_key),

    CONSTRAINT fk_snapshot_property
        FOREIGN KEY (property_key)
        REFERENCES dim_property (property_key),

    CONSTRAINT fk_snapshot_run
        FOREIGN KEY (run_key)
        REFERENCES etl_run (run_key),

    CONSTRAINT uq_snapshot_run_listing
        UNIQUE (run_key, listing_key)
);
