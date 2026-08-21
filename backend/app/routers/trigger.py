from typing import Union
from fastapi import APIRouter, status, HTTPException, Body
from backend.app.schemas.trigger import (
    OpenAQTriggerRequest,
    USGSTriggerRequest,
    TriggerResponse,
)
from backend.app.services.prefect_service import PrefectService

router = APIRouter(prefix="/api", tags=["Trigger"])


@router.post(
    "/trigger",
    response_model=TriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Prefect Pipeline Execution",
    description="Trigger an existing Prefect ETL pipeline (OpenAQ or USGS) asynchronously and return the Prefect flow_run_id.",
)
def trigger_pipeline(
    payload: Union[OpenAQTriggerRequest, USGSTriggerRequest] = Body(..., discriminator="pipeline")
):
    """Trigger OpenAQ or USGS Prefect flow run."""
    pipeline_type = payload.pipeline
    params_dict = payload.model_dump()

    try:
        flow_run_id = PrefectService.trigger_pipeline(pipeline_type, params_dict)
        return TriggerResponse(
            status="triggered",
            pipeline=pipeline_type,
            flow_run_id=flow_run_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger Prefect flow: {e}",
        )
