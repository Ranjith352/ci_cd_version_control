import os
import sys
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy import text
from prefect import task, get_run_logger

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from etl.extraction.usgs_extract import USGSExtractor
from etl.transformation.usgs_transform import USGSTransformer
from etl.loading.load import get_db_engine, load_earthquakes_upsert, log_pipeline_run
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


@task(name="extract_usgs", retries=3, retry_delay_seconds=10)
def extract_usgs_task(
    start_date: str = "2026-01-01",
    end_date: Optional[str] = "2026-08-20",
    min_magnitude: float = 2.5,
    max_magnitude: Optional[float] = None,
    limit: int = 1000,
) -> Dict[str, Any]:
    """Prefect task to extract earthquake events from USGS GeoJSON API."""
    logger = get_run_logger()
    logger.info(f"Starting USGS extraction task: start_date={start_date}, end_date={end_date}, min_mag={min_magnitude}, limit={limit}")

    try:
        extractor = USGSExtractor()
        raw_data = extractor.extract_earthquakes(
            start_date=start_date,
            end_date=end_date,
            min_magnitude=min_magnitude,
            max_magnitude=max_magnitude,
            limit=limit,
        )
        extractor.save_raw_json(raw_data)

        features = raw_data.get("geojson", {}).get("features", [])
        logger.info(f"USGS extraction task completed successfully. Extracted {len(features)} earthquake event features.")
        return raw_data
    except Exception as e:
        logger.error(f"USGS extraction task failed: {e}")
        raise RuntimeError(f"USGS extraction failed: {e}") from e


@task(name="validate_usgs_extraction")
def validate_usgs_extraction_task(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prefect task to validate raw USGS GeoJSON extraction payload."""
    logger = get_run_logger()
    logger.info("Validating raw USGS GeoJSON extraction payload...")

    if not isinstance(raw_data, dict):
        logger.error("USGS extraction payload is not a dictionary.")
        raise ValueError("Invalid USGS raw extraction payload: expected dictionary.")

    geojson = raw_data.get("geojson", {})
    features = geojson.get("features", [])

    if not isinstance(features, list):
        logger.error("USGS GeoJSON features attribute is missing or invalid.")
        raise ValueError("Invalid USGS payload: features is not a list.")

    if len(features) == 0:
        logger.error("USGS extraction returned 0 features. Cannot proceed to transformation.")
        raise ValueError("USGS extraction payload contains 0 features.")

    logger.info(f"USGS extraction validation passed. Count = {len(features)} earthquake events.")
    return raw_data


@task(name="transform_usgs", retries=2, retry_delay_seconds=5)
def transform_usgs_task(raw_data: Dict[str, Any]) -> pd.DataFrame:
    """Prefect task to transform raw USGS GeoJSON data into clean tabular format."""
    logger = get_run_logger()
    logger.info("Starting USGS earthquake data transformation task...")

    try:
        transformer = USGSTransformer()
        flat_df = transformer.extract_flat_features(raw_data)
        clean_df = transformer.transform(flat_df)
        transformer.save_processed_data(clean_df)

        logger.info(f"USGS transformation task completed successfully. Transformed shape: {clean_df.shape}")
        return clean_df
    except Exception as e:
        logger.error(f"USGS transformation task failed: {e}")
        raise RuntimeError(f"USGS transformation failed: {e}") from e


@task(name="validate_usgs_transformation")
def validate_usgs_transformation_task(df: pd.DataFrame) -> pd.DataFrame:
    """Prefect task to validate transformed USGS earthquake DataFrame schema and bounds."""
    logger = get_run_logger()
    logger.info("Validating transformed USGS earthquake DataFrame...")

    if df is None or not isinstance(df, pd.DataFrame):
        logger.error("Transformed USGS data is None or not a DataFrame.")
        raise ValueError("USGS transformation result is not a DataFrame.")

    if df.empty:
        logger.error("Transformed USGS DataFrame is unexpectedly empty.")
        raise ValueError("Transformed USGS DataFrame is empty.")

    required_columns = [
        "event_id", "event_time", "magnitude", "magnitude_type", "place", "region",
        "longitude", "latitude", "depth_km", "magnitude_category", "status", "event_type", "tsunami", "event_url"
    ]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in transformed USGS DataFrame: {missing_cols}")
        raise ValueError(f"USGS DataFrame missing required columns: {missing_cols}")

    # Validate event_ids exist
    if df["event_id"].isnull().any() or (df["event_id"] == "").any():
        logger.error("Found null or empty event_id values in USGS DataFrame.")
        raise ValueError("USGS DataFrame contains invalid event_id values.")

    # Validate magnitude range (-1.0 to 10.0)
    if not pd.api.types.is_numeric_dtype(df["magnitude"]) or ((df["magnitude"] < -1.0) | (df["magnitude"] > 10.0)).any():
        logger.error("USGS magnitude values are out of bounds (-1.0 to 10.0).")
        raise ValueError("USGS DataFrame contains magnitude values out of bounds.")

    # Validate coordinate ranges
    valid_lats = (df["latitude"] >= -90) & (df["latitude"] <= 90)
    valid_lons = (df["longitude"] >= -180) & (df["longitude"] <= 180)
    if not valid_lats.all() or not valid_lons.all():
        logger.error("Found out-of-range coordinates in USGS DataFrame.")
        raise ValueError("USGS DataFrame contains coordinates out of bounds.")

    # Validate depth_km is numeric
    if not pd.api.types.is_numeric_dtype(df["depth_km"]):
        logger.error("USGS depth_km column is not numeric.")
        raise ValueError("USGS DataFrame depth_km column must be numeric.")

    logger.info(f"USGS transformation validation passed. Clean records = {len(df)}.")
    return df


@task(name="load_usgs", retries=2, retry_delay_seconds=5)
def load_usgs_task(df: pd.DataFrame) -> int:
    """Prefect task to load transformed USGS dataset into PostgreSQL with idempotent upsert."""
    logger = get_run_logger()
    logger.info("Starting USGS PostgreSQL database loading task...")

    engine, db_type = get_db_engine()
    if db_type != "postgresql":
        logger.error(f"Required target database is PostgreSQL, but engine connected to '{db_type}'. Fallback to SQLite is disabled.")
        raise RuntimeError("PostgreSQL database connection failed. Silent fallback to SQLite is strictly forbidden.")

    try:
        ensure_schema_exists(engine, db_type)
        loaded_count = load_earthquakes_upsert(engine, df, db_type)
        log_pipeline_run(engine, "Prefect_USGS_ETL", len(df), loaded_count, "SUCCESS")

        logger.info(f"Successfully loaded {loaded_count} USGS earthquake records into PostgreSQL database '{POSTGRES_DB}'.")
        return loaded_count
    except Exception as e:
        logger.error(f"USGS database loading task failed: {e}")
        log_pipeline_run(engine, "Prefect_USGS_ETL", len(df), 0, "FAILED", str(e))
        raise RuntimeError(f"PostgreSQL loading failed for USGS: {e}") from e
