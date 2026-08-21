import os
import sys
from typing import Dict, Any
from prefect import flow, get_run_logger

# Add project root and prefect directory to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PREFECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PREFECT_DIR not in sys.path:
    sys.path.insert(0, PREFECT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tasks.openaq_tasks import (
    extract_openaq_task,
    validate_openaq_extraction_task,
    transform_openaq_task,
    validate_openaq_transformation_task,
    load_openaq_task,
)
from config.config import POSTGRES_DB


@flow(name="openaq_etl_flow")
def openaq_etl_flow(
    city: str = "Coimbatore",
    latitude: float = 11.0168,
    longitude: float = 76.9558,
    radius: int = 25000,
    measurement_limit: int = 2000,
) -> Dict[str, Any]:
    """Prefect flow to orchestrate end-to-end OpenAQ air quality extraction, transformation, validation, and loading."""
    logger = get_run_logger()
    logger.info(
        f"Starting openaq_etl_flow: city='{city}', lat={latitude}, lon={longitude}, "
        f"radius={radius}, measurement_limit={measurement_limit}"
    )

    try:
        # Step 1: Extract OpenAQ data
        raw_data = extract_openaq_task(
            city=city,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            limit=measurement_limit,
        )
        records_extracted = len(raw_data.get("measurements", []))

        # Step 2: Validate extraction result
        validated_raw = validate_openaq_extraction_task(raw_data)

        # Step 3: Transform OpenAQ data
        transformed_df = transform_openaq_task(validated_raw)
        records_transformed = len(transformed_df)

        # Step 4: Validate transformed dataset
        validated_df = validate_openaq_transformation_task(transformed_df)

        # Step 5: Load into PostgreSQL
        records_loaded = load_openaq_task(validated_df)

        result = {
            "status": "success",
            "source": "openaq",
            "city": city,
            "records_extracted": records_extracted,
            "records_transformed": records_transformed,
            "records_loaded": records_loaded,
            "database": POSTGRES_DB,
        }

        logger.info(f"openaq_etl_flow completed successfully! Summary: {result}")
        return result

    except Exception as e:
        logger.error(f"openaq_etl_flow failed with error: {e}")
        raise RuntimeError(f"openaq_etl_flow execution failed: {e}") from e


if __name__ == "__main__":
    openaq_etl_flow()
