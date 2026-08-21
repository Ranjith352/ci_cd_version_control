from fastapi import APIRouter, status, Path
from backend.app.schemas.status import FlowStatusResponse
from backend.app.services.prefect_service import PrefectService

router = APIRouter(prefix="/api", tags=["Status"])


@router.get(
    "/status/{run_id}",
    response_model=FlowStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Prefect Flow Run Status",
    description="Query real-time execution status of a Prefect flow run by flow_run_id.",
)
async def get_flow_status(
    run_id: str = Path(..., description="Prefect flow run unique ID")
):
    """Query Prefect flow run status."""
    status_info = await PrefectService.get_flow_run_status(run_id)
    return FlowStatusResponse(
        flow_run_id=status_info["flow_run_id"],
        status=status_info["status"],
        state_type=status_info["state_type"],
        message=status_info.get("message"),
    )
