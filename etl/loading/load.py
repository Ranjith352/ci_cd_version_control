import logging
import os
import sys
from typing import Dict, Any
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.config import (
    SQLALCHEMY_DATABASE_URI,
    PROCESSED_OPENAQ_DIR,
    PROCESSED_USGS_DIR,
    DATABASE_DIR,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def get_db_engine():
    """Create SQLAlchemy engine for PostgreSQL or fallback to SQLite if PostgreSQL unreachable."""
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Connected to PostgreSQL database at {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        return engine, "postgresql"
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}). Initializing SQLite database fallback for pipeline testing...")
        sqlite_db_path = DATABASE_DIR / "environmental_db.sqlite"
        engine = create_engine(f"sqlite:///{sqlite_db_path}")
        logger.info(f"Connected to SQLite database at {sqlite_db_path}")
        return engine, "sqlite"


def initialize_schema(engine, db_type="postgresql"):
    """Execute DDL schema initialization."""
    schema_file = DATABASE_DIR / "schema.sql"
    if not schema_file.exists():
        logger.error(f"Schema file not found at {schema_file}")
        return

    with open(schema_file, "r", encoding="utf-8") as f:
        sql_script = f.read()

    with engine.begin() as conn:
        if db_type == "sqlite":
            # Adapt PostgreSQL DDL for SQLite compatibility
            sqlite_script = (
                sql_script.replace("TIMESTAMPTZ", "TEXT")
                .replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
                .replace("NUMERIC(10, 6)", "REAL")
                .replace("NUMERIC(12, 4)", "REAL")
                .replace("NUMERIC(4, 2)", "REAL")
                .replace("NUMERIC(8, 2)", "REAL")
                .replace("BIGINT PRIMARY KEY", "INTEGER PRIMARY KEY")
                .replace("ON DELETE CASCADE", "")
                .replace(" CASCADE", "")
            )
            for stmt in sqlite_script.split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))
        else:
            for stmt in sql_script.split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))

    logger.info(f"Database schema initialized successfully on {db_type.upper()}.")


def load_locations_upsert(engine, df_aq: pd.DataFrame, db_type: str = "postgresql") -> int:
    """Extract and upsert unique locations from air quality dataset."""
    loc_cols = ["location_id", "location_name", "city", "country", "latitude", "longitude"]
    df_locs = df_aq[loc_cols].drop_duplicates(subset=["location_id"]).copy()

    records_upserted = 0
    with engine.begin() as conn:
        for _, row in df_locs.iterrows():
            loc_id = int(row["location_id"])
            loc_name = str(row["location_name"])
            city = str(row["city"]) if pd.notna(row["city"]) else None
            country = str(row["country"]) if pd.notna(row["country"]) else None
            lat = float(row["latitude"]) if pd.notna(row["latitude"]) else None
            lon = float(row["longitude"]) if pd.notna(row["longitude"]) else None

            if db_type == "postgresql":
                sql = text("""
                    INSERT INTO locations (location_id, location_name, city, country, latitude, longitude, updated_at)
                    VALUES (:loc_id, :loc_name, :city, :country, :lat, :lon, CURRENT_TIMESTAMP)
                    ON CONFLICT (location_id) DO UPDATE SET
                        location_name = EXCLUDED.location_name,
                        city = EXCLUDED.city,
                        country = EXCLUDED.country,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        updated_at = CURRENT_TIMESTAMP;
                """)
            else:
                sql = text("""
                    INSERT INTO locations (location_id, location_name, city, country, latitude, longitude, updated_at)
                    VALUES (:loc_id, :loc_name, :city, :country, :lat, :lon, CURRENT_TIMESTAMP)
                    ON CONFLICT (location_id) DO UPDATE SET
                        location_name = excluded.location_name,
                        city = excluded.city,
                        country = excluded.country,
                        latitude = excluded.latitude,
                        longitude = excluded.longitude,
                        updated_at = CURRENT_TIMESTAMP;
                """)

            conn.execute(sql, {
                "loc_id": loc_id,
                "loc_name": loc_name,
                "city": city,
                "country": country,
                "lat": lat,
                "lon": lon,
            })
            records_upserted += 1

    logger.info(f"Upserted {records_upserted} location records.")
    return records_upserted


def load_air_quality_upsert(engine, df: pd.DataFrame, db_type: str = "postgresql") -> int:
    """Upsert OpenAQ transformed air quality readings into PostgreSQL/SQLite."""
    # First ensure locations metadata exists
    load_locations_upsert(engine, df, db_type)

    records_upserted = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            m_id = int(row["measurement_id"])
            loc_id = int(row["location_id"])
            loc_name = str(row["location_name"])
            city = str(row["city"]) if pd.notna(row["city"]) else None
            country = str(row["country"]) if pd.notna(row["country"]) else None
            lat = float(row["latitude"]) if pd.notna(row["latitude"]) else None
            lon = float(row["longitude"]) if pd.notna(row["longitude"]) else None
            param = str(row["parameter"])
            val = float(row["value"])
            unit = str(row["unit"])
            norm_val = float(row["normalized_value"]) if pd.notna(row["normalized_value"]) else None
            norm_unit = str(row["normalized_unit"]) if pd.notna(row["normalized_unit"]) else None
            aqi = int(row["aqi_us_epa"]) if pd.notna(row["aqi_us_epa"]) else None
            ts = str(row["datetime"])

            if db_type == "postgresql":
                sql = text("""
                    INSERT INTO air_quality_readings (
                        measurement_id, location_id, location_name, city, country,
                        latitude, longitude, parameter, value, unit,
                        normalized_value, normalized_unit, aqi_us_epa, reading_timestamp
                    )
                    VALUES (
                        :m_id, :loc_id, :loc_name, :city, :country,
                        :lat, :lon, :param, :val, :unit,
                        :norm_val, :norm_unit, :aqi, :ts
                    )
                    ON CONFLICT (measurement_id) DO UPDATE SET
                        value = EXCLUDED.value,
                        normalized_value = EXCLUDED.normalized_value,
                        aqi_us_epa = EXCLUDED.aqi_us_epa,
                        reading_timestamp = EXCLUDED.reading_timestamp;
                """)
            else:
                sql = text("""
                    INSERT INTO air_quality_readings (
                        measurement_id, location_id, location_name, city, country,
                        latitude, longitude, parameter, value, unit,
                        normalized_value, normalized_unit, aqi_us_epa, reading_timestamp
                    )
                    VALUES (
                        :m_id, :loc_id, :loc_name, :city, :country,
                        :lat, :lon, :param, :val, :unit,
                        :norm_val, :norm_unit, :aqi, :ts
                    )
                    ON CONFLICT (measurement_id) DO UPDATE SET
                        value = excluded.value,
                        normalized_value = excluded.normalized_value,
                        aqi_us_epa = excluded.aqi_us_epa,
                        reading_timestamp = excluded.reading_timestamp;
                """)

            conn.execute(sql, {
                "m_id": m_id,
                "loc_id": loc_id,
                "loc_name": loc_name,
                "city": city,
                "country": country,
                "lat": lat,
                "lon": lon,
                "param": param,
                "val": val,
                "unit": unit,
                "norm_val": norm_val,
                "norm_unit": norm_unit,
                "aqi": aqi,
                "ts": ts,
            })
            records_upserted += 1

    logger.info(f"Upserted {records_upserted} air quality reading records into database.")
    return records_upserted


def load_earthquakes_upsert(engine, df: pd.DataFrame, db_type: str = "postgresql") -> int:
    """Upsert USGS transformed earthquake events into PostgreSQL/SQLite."""
    records_upserted = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            event_id = str(row["event_id"])
            event_time = str(row["event_time"])
            mag = float(row["magnitude"])
            mag_type = str(row["magnitude_type"]) if pd.notna(row["magnitude_type"]) else None
            place = str(row["place"]) if pd.notna(row["place"]) else None
            region = str(row["region"]) if pd.notna(row["region"]) else None
            lon = float(row["longitude"])
            lat = float(row["latitude"])
            depth = float(row["depth_km"])
            cat = str(row["magnitude_category"])
            status = str(row["status"]) if pd.notna(row["status"]) else None
            event_type = str(row["event_type"]) if pd.notna(row["event_type"]) else None
            tsunami = int(row["tsunami"]) if pd.notna(row["tsunami"]) else 0
            url = str(row["event_url"]) if pd.notna(row["event_url"]) else None

            if db_type == "postgresql":
                sql = text("""
                    INSERT INTO earthquake_events (
                        event_id, event_time, magnitude, magnitude_type, place, region,
                        longitude, latitude, depth_km, magnitude_category,
                        status, event_type, tsunami, event_url
                    )
                    VALUES (
                        :event_id, :event_time, :mag, :mag_type, :place, :region,
                        :lon, :lat, :depth, :cat,
                        :status, :event_type, :tsunami, :url
                    )
                    ON CONFLICT (event_id) DO UPDATE SET
                        magnitude = EXCLUDED.magnitude,
                        depth_km = EXCLUDED.depth_km,
                        status = EXCLUDED.status,
                        tsunami = EXCLUDED.tsunami;
                """)
            else:
                sql = text("""
                    INSERT INTO earthquake_events (
                        event_id, event_time, magnitude, magnitude_type, place, region,
                        longitude, latitude, depth_km, magnitude_category,
                        status, event_type, tsunami, event_url
                    )
                    VALUES (
                        :event_id, :event_time, :mag, :mag_type, :place, :region,
                        :lon, :lat, :depth, :cat,
                        :status, :event_type, :tsunami, :url
                    )
                    ON CONFLICT (event_id) DO UPDATE SET
                        magnitude = excluded.magnitude,
                        depth_km = excluded.depth_km,
                        status = excluded.status,
                        tsunami = excluded.tsunami;
                """)

            conn.execute(sql, {
                "event_id": event_id,
                "event_time": event_time,
                "mag": mag,
                "mag_type": mag_type,
                "place": place,
                "region": region,
                "lon": lon,
                "lat": lat,
                "depth": depth,
                "cat": cat,
                "status": status,
                "event_type": event_type,
                "tsunami": tsunami,
                "url": url,
            })
            records_upserted += 1

    logger.info(f"Upserted {records_upserted} earthquake records into database.")
    return records_upserted


def log_pipeline_run(engine, pipeline_name: str, extracted: int, loaded: int, status: str, error_msg: str = None):
    """Log pipeline run audit record in pipeline_runs table."""
    try:
        with engine.begin() as conn:
            sql = text("""
                INSERT INTO pipeline_runs (pipeline_name, records_extracted, records_loaded, status, completed_at, error_message)
                VALUES (:name, :extracted, :loaded, :status, CURRENT_TIMESTAMP, :err)
            """)
            conn.execute(sql, {
                "name": pipeline_name,
                "extracted": extracted,
                "loaded": loaded,
                "status": status,
                "err": error_msg,
            })
    except Exception as e:
        logger.warning(f"Could not log pipeline run record: {e}")


def run_complete_loading() -> Dict[str, Any]:
    """Execute end-to-end loading for both OpenAQ and USGS transformed datasets."""
    engine, db_type = get_db_engine()
    initialize_schema(engine, db_type)

    # 1. Load processed OpenAQ data
    openaq_parquet = PROCESSED_OPENAQ_DIR / "openaq_processed.parquet"
    if not openaq_parquet.exists():
        openaq_parquet = PROCESSED_OPENAQ_DIR / "openaq_processed.csv"

    logger.info(f"Reading processed OpenAQ dataset from {openaq_parquet}...")
    if str(openaq_parquet).endswith(".parquet"):
        df_openaq = pd.read_parquet(openaq_parquet)
    else:
        df_openaq = pd.read_csv(openaq_parquet)

    aq_loaded = load_air_quality_upsert(engine, df_openaq, db_type)
    log_pipeline_run(engine, "OpenAQ_ETL", len(df_openaq), aq_loaded, "SUCCESS")

    # 2. Load processed USGS data
    usgs_parquet = PROCESSED_USGS_DIR / "usgs_processed.parquet"
    if not usgs_parquet.exists():
        usgs_parquet = PROCESSED_USGS_DIR / "usgs_processed.csv"

    logger.info(f"Reading processed USGS dataset from {usgs_parquet}...")
    if str(usgs_parquet).endswith(".parquet"):
        df_usgs = pd.read_parquet(usgs_parquet)
    else:
        df_usgs = pd.read_csv(usgs_parquet)

    eq_loaded = load_earthquakes_upsert(engine, df_usgs, db_type)
    log_pipeline_run(engine, "USGS_ETL", len(df_usgs), eq_loaded, "SUCCESS")

    summary = {
        "db_type": db_type,
        "openaq_records_loaded": aq_loaded,
        "usgs_records_loaded": eq_loaded,
    }
    logger.info(f"Database loading completed successfully! Summary: {summary}")
    return summary


if __name__ == "__main__":
    run_complete_loading()
