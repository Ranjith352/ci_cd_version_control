import json
import logging
import os
import glob
import re
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.config import RAW_USGS_DIR, PROCESSED_USGS_DIR

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def categorize_magnitude(mag: float) -> str:
    """Classify earthquake magnitude into standard analytical buckets."""
    if pd.isna(mag):
        return "Unknown"
    m = float(mag)
    if m < 2.0:
        return "Micro"
    elif 2.0 <= m <= 3.9:
        return "Minor"
    elif 4.0 <= m <= 4.9:
        return "Light"
    elif 5.0 <= m <= 5.9:
        return "Moderate"
    elif 6.0 <= m <= 6.9:
        return "Strong"
    elif 7.0 <= m <= 7.9:
        return "Major"
    else: # m >= 8.0
        return "Great"


def extract_region_from_place(place: Optional[str]) -> str:
    """Extract a clean geographic region name from USGS place description."""
    if not place or not isinstance(place, str):
        return "Unknown Region"

    p = place.strip()
    if " of " in p:
        region_part = p.split(" of ", 1)[1].strip()
    else:
        region_part = p

    # State code mapping for US locations
    us_state_codes = {
        "CA": "California, USA",
        "AK": "Alaska, USA",
        "NV": "Nevada, USA",
        "HI": "Hawaii, USA",
        "OR": "Oregon, USA",
        "WA": "Washington, USA",
        "UT": "Utah, USA",
        "TX": "Texas, USA",
        "PR": "Puerto Rico",
        "VI": "Virgin Islands",
        "OK": "Oklahoma, USA",
        "MT": "Montana, USA",
        "WY": "Wyoming, USA",
        "ID": "Idaho, USA",
    }

    if "," in region_part:
        parts = [pt.strip() for pt in region_part.split(",")]
        sub_region = parts[0]
        country_code = parts[-1]

        if country_code in us_state_codes:
            return us_state_codes[country_code]
        return f"{sub_region}, {country_code}"
    
    return region_part


class USGSTransformer:
    """Transformer for raw USGS GeoJSON data into clean tabular format."""

    def __init__(self, raw_dir=RAW_USGS_DIR, processed_dir=PROCESSED_USGS_DIR):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir

    def load_latest_raw_json(self) -> Dict[str, Any]:
        """Load the most recent raw USGS JSON file from data/raw/usgs/."""
        json_files = sorted(glob.glob(str(self.raw_dir / "usgs_raw_*.json")))
        if not json_files:
            raise FileNotFoundError(f"No USGS raw JSON files found in {self.raw_dir}")

        latest_file = json_files[-1]
        logger.info(f"Loading raw USGS JSON: {latest_file}")
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def extract_flat_features(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Extract earthquake features from GeoJSON into a Pandas DataFrame."""
        geojson = raw_data.get("geojson", {})
        features = geojson.get("features", [])

        records = []
        for feat in features:
            event_id = feat.get("id")
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [None, None, None])

            lon = coords[0] if len(coords) > 0 else None
            lat = coords[1] if len(coords) > 1 else None
            depth = coords[2] if len(coords) > 2 else None

            records.append({
                "event_id": str(event_id) if event_id else None,
                "event_time_epoch_ms": props.get("time"),
                "magnitude": props.get("mag"),
                "magnitude_type": props.get("magType"),
                "place": props.get("place"),
                "longitude": float(lon) if lon is not None else np.nan,
                "latitude": float(lat) if lat is not None else np.nan,
                "depth_km": float(depth) if depth is not None else np.nan,
                "status": props.get("status"),
                "event_type": props.get("type"),
                "tsunami": int(props.get("tsunami", 0)),
                "event_url": props.get("url"),
            })

        df = pd.DataFrame(records)
        logger.info(f"Extracted {len(df)} feature records from GeoJSON.")
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean data, deduplicate, convert datetimes, and derive categories."""
        logger.info("Executing USGS earthquake data transformations...")

        initial_count = len(df)

        # 1. Clean missing core keys
        df = df.dropna(subset=["event_id", "event_time_epoch_ms", "magnitude", "latitude", "longitude"]).copy()
        logger.info(f"Dropped {initial_count - len(df)} records missing core fields.")

        # 2. Deduplicate using unique event_id
        df = df.drop_duplicates(subset=["event_id"]).copy()
        logger.info(f"Retained {len(df)} records after deduplication by event_id.")

        # 3. Convert epoch timestamp (ms) to UTC ISO datetime string
        df["event_time"] = pd.to_datetime(df["event_time_epoch_ms"], unit="ms", utc=True)
        df["event_time"] = df["event_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        df.drop(columns=["event_time_epoch_ms"], inplace=True)

        # 4. Validate coordinate and numeric bounds
        df = df[
            (df["latitude"] >= -90) & (df["latitude"] <= 90) &
            (df["longitude"] >= -180) & (df["longitude"] <= 180) &
            (df["magnitude"] >= -1.0) & (df["magnitude"] <= 10.0)
        ].copy()

        # 5. Derive magnitude categories
        df["magnitude_category"] = df["magnitude"].apply(categorize_magnitude)

        # 6. Derive region tagging
        df["region"] = df["place"].apply(extract_region_from_place)

        # Reorder columns matching target schema
        final_cols = [
            "event_id",
            "event_time",
            "magnitude",
            "magnitude_type",
            "place",
            "region",
            "longitude",
            "latitude",
            "depth_km",
            "magnitude_category",
            "status",
            "event_type",
            "tsunami",
            "event_url",
        ]

        df = df[final_cols].copy()
        logger.info(f"USGS transformation complete. Final shape: {df.shape}")
        return df

    def save_processed_data(self, df: pd.DataFrame) -> tuple:
        """Save clean DataFrame as CSV and Parquet in data/processed/usgs/."""
        csv_path = self.processed_dir / "usgs_processed.csv"
        parquet_path = self.processed_dir / "usgs_processed.parquet"

        df.to_csv(csv_path, index=False, encoding="utf-8")
        df.to_parquet(parquet_path, index=False)

        logger.info(f"Saved processed USGS dataset to:\n  - CSV: {csv_path}\n  - Parquet: {parquet_path}")
        return str(csv_path), str(parquet_path)


def run_usgs_transformation() -> tuple:
    """Entry point function for USGS earthquake transformation."""
    transformer = USGSTransformer()
    raw_data = transformer.load_latest_raw_json()
    flat_df = transformer.extract_flat_features(raw_data)
    clean_df = transformer.transform(flat_df)
    csv_path, parquet_path = transformer.save_processed_data(clean_df)
    return csv_path, parquet_path


if __name__ == "__main__":
    run_usgs_transformation()
