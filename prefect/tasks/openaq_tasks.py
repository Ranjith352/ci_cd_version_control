import os
import sys
from typing import Dict, Any
import pandas as pd
from sqlalchemy import text
from prefect import task, get_run_logger

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from etl.extraction.openaq_extract import OpenAQExtractor
from etl.transformation.openaq_transform import OpenAQTransformer
from etl.loading.load import get_db_engine, load_air_quality_upsert, log_pipeline_run
from config.config import POSTGRES_DB


def ensure_schema_exists(engine, db_type: str = "postgresql"):
    """Ensure relational tables exist in database without dropping existing data."""
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS locations (
            location_id INT PRIMARY KEY,
            location_name VARCHAR(255) NOT NULL,
            city VARCHAR(100),
            country VARCHAR(100),
            latitude NUMERIC(10, 6),
            longitude NUMERIC(10, 6),
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS air_quality_readings (
            measurement_id BIGINT PRIMARY KEY,
            location_id INT NOT NULL REFERENCES locations(location_id) ON DELETE CASCADE,
            location_name VARCHAR(255),
            city VARCHAR(100),
            country VARCHAR(100),
            latitude NUMERIC(10, 6),
            longitude NUMERIC(10, 6),
            parameter VARCHAR(50) NOT NULL,
            value NUMERIC(12, 4) NOT NULL,
            unit VARCHAR(50) NOT NULL,
            normalized_value NUMERIC(12, 4),
            normalized_unit VARCHAR(50),
            aqi_us_epa INT,
            reading_timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT idx_unique_aq_reading UNIQUE (location_id, parameter, reading_timestamp)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS earthquake_events (
            event_id VARCHAR(50) PRIMARY KEY,
            event_time TIMESTAMPTZ NOT NULL,
            magnitude NUMERIC(4, 2) NOT NULL,
            magnitude_type VARCHAR(20),
            place VARCHAR(255),
            region VARCHAR(150),
            longitude NUMERIC(10, 6) NOT NULL,
            latitude NUMERIC(10, 6) NOT NULL,
            depth_km NUMERIC(8, 2) NOT NULL,
            magnitude_category VARCHAR(30) NOT NULL,
            status VARCHAR(50),
            event_type VARCHAR(50),
            tsunami INT DEFAULT 0,
            event_url TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id SERIAL PRIMARY KEY,
            pipeline_name VARCHAR(100) NOT NULL,
            records_extracted INT DEFAULT 0,
            records_loaded INT DEFAULT 0,
            status VARCHAR(50) NOT NULL,
            started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMPTZ,
            error_message TEXT
        );
        """,
    ]
    with engine.begin() as conn:
        for stmt in ddl_statements:
            conn.execute(text(stmt))


@task(name="extract_openaq", retries=3, retry_delay_seconds=10)
def extract_openaq_task(
    city: str = "Coimbatore",
    latitude: float = 11.0168,
    longitude: float = 76.9558,
    radius: int = 25000,
    limit: int = 2000,
) -> Dict[str, Any]:
    """Prefect task to extract raw air quality data from OpenAQ v3 API."""
    logger = get_run_logger()
    logger.info(f"Starting OpenAQ extraction task for city='{city}', coords=({latitude}, {longitude}), radius={radius}m")

    try:
        extractor = OpenAQExtractor()
        raw_data = extractor.extract_location_data(
            city=city,
            coordinates=(latitude, longitude),
            limit_locations=15,
        )
        extractor.save_raw_json(raw_data)

        meas_count = len(raw_data.get("measurements", []))
        logger.info(f"OpenAQ extraction task completed successfully. Extracted {meas_count} raw measurement records.")
        return raw_data
    except Exception as e:
        logger.error(f"OpenAQ extraction task failed: {e}")
        raise RuntimeError(f"OpenAQ extraction failed: {e}") from e


@task(name="validate_openaq_extraction")
def validate_openaq_extraction_task(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prefect task to validate raw OpenAQ extraction payload before transformation."""
    logger = get_run_logger()
    logger.info("Validating raw OpenAQ extraction output...")

    if not isinstance(raw_data, dict):
        logger.error("OpenAQ raw extraction payload is not a valid dictionary structure.")
        raise ValueError("Invalid OpenAQ raw extraction payload: expected dictionary.")

    measurements = raw_data.get("measurements", [])
    if not isinstance(measurements, list):
        logger.error("OpenAQ raw extraction measurements attribute is not a list.")
        raise ValueError("Invalid OpenAQ extraction payload: measurements attribute missing or invalid.")

    if len(measurements) == 0:
        logger.error("OpenAQ extraction returned 0 measurements. Cannot proceed to transformation.")
        raise ValueError("OpenAQ extraction payload contains 0 measurements.")

    logger.info(f"OpenAQ extraction validation passed. Count = {len(measurements)} raw records.")
    return raw_data


@task(name="transform_openaq", retries=2, retry_delay_seconds=5)
def transform_openaq_task(raw_data: Dict[str, Any]) -> pd.DataFrame:
    """Prefect task to clean, normalize units (ppm -> µg/m³), and compute EPA AQI."""
    logger = get_run_logger()
    logger.info("Starting OpenAQ data transformation task...")

    try:
        transformer = OpenAQTransformer()
        flat_df = transformer.extract_flat_records(raw_data)
        clean_df = transformer.transform(flat_df)
        transformer.save_processed_data(clean_df)

        logger.info(f"OpenAQ transformation task completed successfully. Transformed shape: {clean_df.shape}")
        return clean_df
    except Exception as e:
        logger.error(f"OpenAQ transformation task failed: {e}")
        raise RuntimeError(f"OpenAQ transformation failed: {e}") from e


@task(name="validate_openaq_transformation")
def validate_openaq_transformation_task(df: pd.DataFrame) -> pd.DataFrame:
    """Prefect task to validate transformed OpenAQ dataset schema, numeric bounds, and timestamps."""
    logger = get_run_logger()
    logger.info("Validating transformed OpenAQ DataFrame...")

    if df is None or not isinstance(df, pd.DataFrame):
        logger.error("Transformed OpenAQ data is None or not a DataFrame.")
        raise ValueError("OpenAQ transformation result is not a DataFrame.")

    if df.empty:
        logger.error("Transformed OpenAQ DataFrame is unexpectedly empty.")
        raise ValueError("Transformed OpenAQ DataFrame is empty.")

    required_columns = [
        "measurement_id", "location_id", "location_name", "city", "country",
        "latitude", "longitude", "parameter", "value", "unit",
        "normalized_value", "normalized_unit", "aqi_us_epa", "datetime"
    ]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in transformed OpenAQ DataFrame: {missing_cols}")
        raise ValueError(f"OpenAQ DataFrame missing required columns: {missing_cols}")

    # Validate measurement_ids exist
    if df["measurement_id"].isnull().any():
        logger.error("Found null measurement_id values in transformed OpenAQ DataFrame.")
        raise ValueError("OpenAQ DataFrame contains null measurement_id values.")

    # Validate values are numeric and non-negative
    if not pd.api.types.is_numeric_dtype(df["value"]) or (df["value"] < 0).any():
        logger.error("OpenAQ value column contains invalid or negative numbers.")
        raise ValueError("OpenAQ DataFrame contains invalid or negative measurement values.")

    # Validate coordinates bounds if present
    valid_lats = df["latitude"].isna() | ((df["latitude"] >= -90) & (df["latitude"] <= 90))
    valid_lons = df["longitude"].isna() | ((df["longitude"] >= -180) & (df["longitude"] <= 180))
    if not valid_lats.all() or not valid_lons.all():
        logger.error("Found out-of-range coordinates in OpenAQ DataFrame.")
        raise ValueError("OpenAQ DataFrame contains coordinates out of bounds (-90..90, -180..180).")

    logger.info(f"OpenAQ transformation validation passed. Clean records = {len(df)}.")
    return df


@task(name="load_openaq", retries=2, retry_delay_seconds=5)
def load_openaq_task(df: pd.DataFrame) -> int:
    """Prefect task to load transformed OpenAQ dataset into PostgreSQL with idempotent upsert."""
    logger = get_run_logger()
    logger.info("Starting OpenAQ PostgreSQL database loading task...")

    engine, db_type = get_db_engine()
    if db_type != "postgresql":
        logger.error(f"Required target database is PostgreSQL, but engine connected to '{db_type}'. Fallback to SQLite is disabled.")
        raise RuntimeError("PostgreSQL database connection failed. Silent fallback to SQLite is strictly forbidden.")

    try:
        ensure_schema_exists(engine, db_type)
        loaded_count = load_air_quality_upsert(engine, df, db_type)
        log_pipeline_run(engine, "Prefect_OpenAQ_ETL", len(df), loaded_count, "SUCCESS")

        logger.info(f"Successfully loaded {loaded_count} OpenAQ records into PostgreSQL database '{POSTGRES_DB}'.")
        return loaded_count
    except Exception as e:
        logger.error(f"OpenAQ database loading task failed: {e}")
        log_pipeline_run(engine, "Prefect_OpenAQ_ETL", len(df), 0, "FAILED", str(e))
        raise RuntimeError(f"PostgreSQL loading failed for OpenAQ: {e}") from e
