from typing import Optional, Literal, Union, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class OpenAQTriggerRequest(BaseModel):
    """Pydantic schema for OpenAQ pipeline execution request."""
    pipeline: Literal["openaq"] = Field(..., description="Pipeline name must be 'openaq'")
    city: str = Field("Coimbatore", min_length=1, description="Target city name")
    latitude: float = Field(11.0168, ge=-90.0, le=90.0, description="Latitude coordinate (-90 to 90)")
    longitude: float = Field(76.9558, ge=-180.0, le=180.0, description="Longitude coordinate (-180 to 180)")
    radius: int = Field(25000, gt=0, description="Search radius in meters (> 0)")
    measurement_limit: int = Field(2000, gt=0, description="Maximum measurement observation count (> 0)")


class USGSTriggerRequest(BaseModel):
    """Pydantic schema for USGS earthquake pipeline execution request."""
    pipeline: Literal["usgs"] = Field(..., description="Pipeline name must be 'usgs'")
    start_date: str = Field("2026-01-01", description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    min_magnitude: float = Field(2.5, ge=-1.0, le=10.0, description="Minimum magnitude threshold (-1.0 to 10.0)")
    max_magnitude: Optional[float] = Field(None, ge=-1.0, le=10.0, description="Maximum magnitude threshold")
    limit: int = Field(1000, gt=0, description="Maximum earthquake event count (> 0)")

    @model_validator(mode="after")
    def validate_dates_and_magnitudes(self):
        # Validate date formats
        try:
            d_start = datetime.strptime(self.start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("start_date must be in ISO format YYYY-MM-DD")

        if self.end_date:
            try:
                d_end = datetime.strptime(self.end_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("end_date must be in ISO format YYYY-MM-DD")
            if d_start > d_end:
                raise ValueError("start_date must be less than or equal to end_date")

        if self.max_magnitude is not None and self.max_magnitude < self.min_magnitude:
            raise ValueError("max_magnitude must be greater than or equal to min_magnitude")

        return self


class TriggerResponse(BaseModel):
    """Response schema returned upon successfully triggering a Prefect pipeline."""
    status: str = Field("triggered", description="Execution status ('triggered')")
    pipeline: str = Field(..., description="Pipeline name ('openaq' or 'usgs')")
    flow_run_id: str = Field(..., description="Prefect flow run unique ID")
