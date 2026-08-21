import json
import logging
import os
import glob
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.config import RAW_OPENAQ_DIR, PROCESSED_OPENAQ_DIR

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# US EPA AQI Breakpoints for PM2.5 (µg/m³) and PM10 (µg/m³)
PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 500.4, 301, 500),
]

PM10_BREAKPOINTS = [
    (0.0, 54.0, 0, 50),
    (54.1, 154.0, 51, 100),
    (154.1, 254.0, 101, 150),
    (254.1, 354.0, 151, 200),
    (354.1, 424.0, 201, 300),
    (424.1, 604.0, 301, 500),
]


def calculate_sub_aqi(concentration: float, breakpoints: List[tuple]) -> Optional[int]:
    """Calculate US EPA AQI sub-index for a concentration given breakpoints."""
    if pd.isna(concentration) or concentration < 0:
        return None

    c = float(concentration)
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= c <= c_high:
            aqi = ((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low
            return int(round(aqi))

    if c > breakpoints[-1][1]:
        return 500
    return 0


class OpenAQTransformer:
    """Transformer for raw OpenAQ JSON data into clean tabular format."""

    def __init__(self, raw_dir=RAW_OPENAQ_DIR, processed_dir=PROCESSED_OPENAQ_DIR):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir

    def load_latest_raw_json(self) -> Dict[str, Any]:
        """Load the most recent raw JSON file from data/raw/openaq/."""
        json_files = sorted(glob.glob(str(self.raw_dir / "openaq_raw_*.json")))
        if not json_files:
            raise FileNotFoundError(f"No OpenAQ raw JSON files found in {self.raw_dir}")

        latest_file = json_files[-1]
        logger.info(f"Loading raw OpenAQ JSON: {latest_file}")
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def extract_flat_records(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Flatten OpenAQ v3 JSON measurement records into a Pandas DataFrame."""
        measurements = raw_data.get("measurements", [])
        locations = {loc["id"]: loc for loc in raw_data.get("locations", []) if isinstance(loc, dict) and "id" in loc}

        records = []
        for index, m in enumerate(measurements):
            loc_id = m.get("location_id") or m.get("locationId") or 0
            loc_meta = locations.get(loc_id, {})

            loc_name = m.get("location_name") or m.get("location") or loc_meta.get("name") or "Unknown Station"
            city = m.get("city") or loc_meta.get("locality") or "Coimbatore"
            
            country_val = m.get("country") or loc_meta.get("country")
            country = country_val if isinstance(country_val, str) else (country_val.get("name") if isinstance(country_val, dict) else "India")

            lat = m.get("latitude")
            if lat is None:
                coords = loc_meta.get("coordinates") or {}
                lat = coords.get("latitude") if isinstance(coords, dict) else None

            lon = m.get("longitude")
            if lon is None:
                coords = loc_meta.get("coordinates") or {}
                lon = coords.get("longitude") if isinstance(coords, dict) else None

            param = m.get("parameter")
            if isinstance(param, dict):
                param_name = param.get("name")
                unit_name = param.get("units")
            else:
                param_name = str(param) if param else None
                unit_name = m.get("unit") or m.get("units")

            val = m.get("value")
            dt_raw = m.get("datetime_utc") or m.get("datetime") or m.get("datetime_local")
            if isinstance(dt_raw, dict):
                dt_raw = dt_raw.get("utc") or dt_raw.get("local")

            # Deterministic unique measurement ID
            m_id = m.get("measurement_id") or (100000 + index)

            records.append({
                "measurement_id": int(m_id),
                "location_id": int(loc_id),
                "location_name": str(loc_name),
                "city": str(city),
                "country": str(country),
                "latitude": float(lat) if lat is not None else np.nan,
                "longitude": float(lon) if lon is not None else np.nan,
                "parameter": str(param_name).lower() if param_name else None,
                "value": float(val) if val is not None else np.nan,
                "unit": str(unit_name) if unit_name else "µg/m³",
                "datetime_raw": dt_raw,
            })

        df = pd.DataFrame(records)
        logger.info(f"Flattened {len(df)} raw measurement records.")
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Perform data cleaning, unit normalization, and AQI computation."""
        logger.info("Executing OpenAQ data transformations...")

        if df.empty:
            logger.warning("Empty DataFrame provided to OpenAQ transform. Returning empty schema DataFrame.")
            empty_cols = [
                "measurement_id", "location_id", "location_name", "city", "country",
                "latitude", "longitude", "parameter", "value", "unit",
                "normalized_value", "normalized_unit", "aqi_us_epa", "datetime"
            ]
            return pd.DataFrame(columns=empty_cols)

        # 1. Clean missing essential fields
        initial_len = len(df)
        df = df.dropna(subset=["location_id", "parameter", "value", "datetime_raw"]).copy()
        logger.info(f"Dropped {initial_len - len(df)} records missing key fields.")

        # 2. Parse and normalize timestamps to UTC ISO strings
        df["datetime"] = pd.to_datetime(df["datetime_raw"], errors="coerce", utc=True)
        df = df.dropna(subset=["datetime"]).copy()
        df["datetime"] = df["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        df.drop(columns=["datetime_raw"], inplace=True)

        # 3. Validate numeric boundaries
        df = df[(df["value"] >= 0)].copy()
        df = df[(df["latitude"].isna()) | ((df["latitude"] >= -90) & (df["latitude"] <= 90))].copy()
        df = df[(df["longitude"].isna()) | ((df["longitude"] >= -180) & (df["longitude"] <= 180))].copy()

        # 4. Remove duplicate observations
        df = df.drop_duplicates(subset=["location_id", "parameter", "datetime"]).copy()
        logger.info(f"Retained {len(df)} clean records after deduplication.")

        # 5. Unit Normalization & Parameter Standardization
        df["unit"] = df["unit"].replace({"ug/m3": "µg/m³", "µg/m3": "µg/m³", "PPM": "ppm", "PPB": "ppb"})

        # Molecular Weight conversion factors at 25°C, 1 atm
        mw_factors = {
            "no2": 1880.0,
            "so2": 2620.0,
            "o3": 1960.0,
            "co": 1145.0,
        }

        normalized_values = []
        normalized_units = []

        for _, row in df.iterrows():
            param = str(row["parameter"]).lower()
            val = row["value"]
            u = row["unit"]

            if u == "ppm" and param in mw_factors:
                val_norm = round(val * mw_factors[param], 3)
                u_norm = "µg/m³"
            elif u == "ppb" and param in mw_factors:
                val_norm = round((val / 1000.0) * mw_factors[param], 3)
                u_norm = "µg/m³"
            else:
                val_norm = val
                u_norm = u

            normalized_values.append(val_norm)
            normalized_units.append(u_norm)

        df["normalized_value"] = normalized_values
        df["normalized_unit"] = normalized_units

        # 6. Calculate US EPA AQI Sub-Indices
        aqi_values = []
        for _, row in df.iterrows():
            param = str(row["parameter"]).lower()
            val = row["normalized_value"]
            u = row["normalized_unit"]

            if param in ["pm25", "pm2.5"] and u == "µg/m³":
                aqi = calculate_sub_aqi(val, PM25_BREAKPOINTS)
            elif param in ["pm10"] and u == "µg/m³":
                aqi = calculate_sub_aqi(val, PM10_BREAKPOINTS)
            else:
                aqi = None
            aqi_values.append(aqi)

        df["aqi_us_epa"] = aqi_values

        final_cols = [
            "measurement_id",
            "location_id",
            "location_name",
            "city",
            "country",
            "latitude",
            "longitude",
            "parameter",
            "value",
            "unit",
            "normalized_value",
            "normalized_unit",
            "aqi_us_epa",
            "datetime",
        ]

        df = df[final_cols].copy()
        logger.info(f"Transformation complete. Final OpenAQ shape: {df.shape}")
        return df

    def save_processed_data(self, df: pd.DataFrame) -> tuple:
        """Save clean DataFrame as CSV and Parquet in data/processed/openaq/."""
        csv_path = self.processed_dir / "openaq_processed.csv"
        parquet_path = self.processed_dir / "openaq_processed.parquet"

        df.to_csv(csv_path, index=False, encoding="utf-8")
        df.to_parquet(parquet_path, index=False)

        logger.info(f"Saved processed OpenAQ dataset to:\n  - CSV: {csv_path}\n  - Parquet: {parquet_path}")
        return str(csv_path), str(parquet_path)


def run_openaq_transformation() -> tuple:
    """Entry point function for OpenAQ transformation."""
    transformer = OpenAQTransformer()
    raw_data = transformer.load_latest_raw_json()
    flat_df = transformer.extract_flat_records(raw_data)
    clean_df = transformer.transform(flat_df)
    csv_path, parquet_path = transformer.save_processed_data(clean_df)
    return csv_path, parquet_path


if __name__ == "__main__":
    run_openaq_transformation()
