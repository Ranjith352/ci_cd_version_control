from typing import Optional
from pydantic import BaseModel, Field


class FlowStatusResponse(BaseModel):
    """Pydantic schema for Prefect flow run status response."""
    flow_run_id: str = Field(..., description="Unique Prefect flow run ID")
    status: str = Field(..., description="Flow state status name (e.g. COMPLETED, RUNNING, FAILED)")
    state_type: str = Field(..., description="Prefect state type indicator")
    message: Optional[str] = Field(None, description="Human-readable state transition message or error details")
