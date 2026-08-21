import os
import sys
from typing import Dict, Any, Optional
from prefect import flow, get_run_logger

# Add project root and prefect directory to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PREFECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PREFECT_DIR not in sys.path:
    sys.path.insert(0, PREFECT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tasks.usgs_tasks import (
    extract_usgs_task,
    validate_usgs_extraction_task,
    transform_usgs_task,
    validate_usgs_transformation_task,
    load_usgs_task,
)
from config.config import POSTGRES_DB


@flow(name="usgs_etl_flow")
def usgs_etl_flow(
    start_date: str = "2026-01-01",
    end_date: Optional[str] = "2026-08-20",
    min_magnitude: float = 2.5,
    max_magnitude: Optional[float] = None,
    limit: int = 1000,
) -> Dict[str, Any]:
    """Prefect flow to orchestrate end-to-end USGS earthquake extraction, transformation, validation, and loading."""
    logger = get_run_logger()
    logger.info(
        f"Starting usgs_etl_flow: start_date={start_date}, end_date={end_date}, "
        f"min_magnitude={min_magnitude}, max_magnitude={max_magnitude}, limit={limit}"
    )

    try:
        # Step 1: Extract USGS GeoJSON data
        raw_data = extract_usgs_task(
            start_date=start_date,
            end_date=end_date,
            min_magnitude=min_magnitude,
            max_magnitude=max_magnitude,
            limit=limit,
        )
        features = raw_data.get("geojson", {}).get("features", [])
        records_extracted = len(features)

        # Step 2: Validate extraction payload
        validated_raw = validate_usgs_extraction_task(raw_data)

        # Step 3: Transform USGS earthquake data
        transformed_df = transform_usgs_task(validated_raw)
        records_transformed = len(transformed_df)

        # Step 4: Validate transformed dataset
        validated_df = validate_usgs_transformation_task(transformed_df)

        # Step 5: Load into PostgreSQL
        records_loaded = load_usgs_task(validated_df)

        result = {
            "status": "success",
            "source": "usgs",
            "start_date": start_date,
            "end_date": end_date,
            "records_extracted": records_extracted,
            "records_transformed": records_transformed,
            "records_loaded": records_loaded,
            "database": POSTGRES_DB,
        }

        logger.info(f"usgs_etl_flow completed successfully! Summary: {result}")
        return result

    except Exception as e:
        logger.error(f"usgs_etl_flow failed with error: {e}")
        raise RuntimeError(f"usgs_etl_flow execution failed: {e}") from e


if __name__ == "__main__":
    usgs_etl_flow()
