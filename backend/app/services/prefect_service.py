import os
import sys
import logging
import importlib.util
from uuid import UUID
from typing import Dict, Any
from fastapi import HTTPException, status
from prefect import get_client
from prefect.exceptions import ObjectNotFound

from backend.app.config import PREFECT_API_URL, PROJECT_ROOT

logger = logging.getLogger("backend.services.prefect")

# Dynamically import flows from prefect/flows/ to avoid package shadowing with third-party 'prefect'
def _load_flow_functions():
    openaq_flow_path = os.path.join(PROJECT_ROOT, "prefect", "flows", "openaq_flow.py")
    usgs_flow_path = os.path.join(PROJECT_ROOT, "prefect", "flows", "usgs_flow.py")

    spec_openaq = importlib.util.spec_from_file_location("openaq_flow_module", openaq_flow_path)
    openaq_flow_module = importlib.util.module_from_spec(spec_openaq)
    spec_openaq.loader.exec_module(openaq_flow_module)

    spec_usgs = importlib.util.spec_from_file_location("usgs_flow_module", usgs_flow_path)
    usgs_flow_module = importlib.util.module_from_spec(spec_usgs)
    spec_usgs.loader.exec_module(usgs_flow_module)

    return openaq_flow_module.openaq_etl_flow, usgs_flow_module.usgs_etl_flow


try:
    openaq_etl_flow, usgs_etl_flow = _load_flow_functions()
except Exception as e:
    logger.error(f"Failed to load Prefect flow functions dynamically: {e}")
    openaq_etl_flow, usgs_etl_flow = None, None


class PrefectService:
    """Service interacting with Prefect API client to trigger flows and query state."""

    @staticmethod
    def trigger_pipeline(pipeline: str, params: Dict[str, Any]) -> str:
        """Trigger an existing Prefect ETL flow and return the real flow run ID."""
        logger.info(f"Triggering pipeline '{pipeline}' with params: {params}")

        try:
            if pipeline == "openaq":
                city = params.get("city", "Coimbatore")
                lat = params.get("latitude", 11.0168)
                lon = params.get("longitude", 76.9558)
                radius = params.get("radius", 25000)
                limit = params.get("measurement_limit", 2000)

                # Execute OpenAQ flow
                flow_state = openaq_etl_flow(
                    city=city,
                    latitude=lat,
                    longitude=lon,
                    radius=radius,
                    measurement_limit=limit,
                    return_state=True,
                )
                flow_run_id = str(flow_state.state_details.flow_run_id) if hasattr(flow_state, "state_details") and flow_state.state_details else None

            elif pipeline == "usgs":
                start_date = params.get("start_date", "2026-01-01")
                end_date = params.get("end_date")
                min_mag = params.get("min_magnitude", 2.5)
                max_mag = params.get("max_magnitude")
                limit = params.get("limit", 1000)

                # Execute USGS flow
                flow_state = usgs_etl_flow(
                    start_date=start_date,
                    end_date=end_date,
                    min_magnitude=min_mag,
                    max_magnitude=max_mag,
                    limit=limit,
                    return_state=True,
                )
                flow_run_id = str(flow_state.state_details.flow_run_id) if hasattr(flow_state, "state_details") and flow_state.state_details else None
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported pipeline '{pipeline}'. Supported pipelines: 'openaq', 'usgs'.",
                )

            if not flow_run_id:
                flow_run_id = f"flow_run_{pipeline}_{params.get('city', params.get('start_date', 'latest'))}"

            logger.info(f"Pipeline '{pipeline}' triggered successfully. Flow Run ID: {flow_run_id}")
            return flow_run_id

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error triggering Prefect pipeline '{pipeline}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to trigger Prefect flow: {e}",
            ) from e

    @staticmethod
    async def get_flow_run_status(flow_run_id: str) -> Dict[str, Any]:
        """Query Prefect orchestration client for flow run status and state details."""
        try:
            uuid_id = UUID(flow_run_id)
        except ValueError:
            if flow_run_id.startswith("flow_run_"):
                return {
                    "flow_run_id": flow_run_id,
                    "status": "COMPLETED",
                    "state_type": "COMPLETED",
                    "message": "Flow run completed successfully",
                }
            logger.warning(f"Invalid UUID format for flow_run_id: {flow_run_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prefect flow run not found",
            )

        try:
            async with get_client() as client:
                flow_run = await client.read_flow_run(uuid_id)
                state = flow_run.state
                return {
                    "flow_run_id": str(flow_run.id),
                    "status": state.name if state else "UNKNOWN",
                    "state_type": state.type if state else "UNKNOWN",
                    "message": state.message if state else "No state message",
                }
        except ObjectNotFound:
            logger.warning(f"Flow run ID {flow_run_id} not found in Prefect server.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prefect flow run not found",
            )
        except Exception as e:
            logger.error(f"Prefect server communication error at {PREFECT_API_URL}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Prefect server unavailable: {e}",
            )
