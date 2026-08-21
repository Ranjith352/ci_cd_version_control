from typing import Optional
from fastapi import APIRouter, status, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db_session
from backend.app.schemas.visualization import (
    AirQualityVisualizationResponse,
    EarthquakeVisualizationResponse,
    AnalyticsTrendsResponse,
)
from backend.app.services.visualization_service import VisualizationService

router = APIRouter(prefix="/api", tags=["Visualization & Analytics"])


@router.get(
    "/visualization/air-quality",
    response_model=AirQualityVisualizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Air Quality Visualization Data",
    description="Query PostgreSQL for aggregated daily air quality concentration averages and EPA AQI sub-indices.",
)
def get_air_quality_visualization(
    city: str = Query("Coimbatore", description="Target city name"),
    parameter: str = Query("pm25", description="Pollutant parameter (e.g. pm25, pm10, no2)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db_session),
):
    """Fetch daily air quality daily concentration data from PostgreSQL."""
    data = VisualizationService.get_air_quality_visualization(
        session=db,
        city=city,
        parameter=parameter,
        start_date=start_date,
        end_date=end_date,
    )
    return AirQualityVisualizationResponse(**data)


@router.get(
    "/visualization/earthquakes",
    response_model=EarthquakeVisualizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Earthquake Hazards Visualization Data",
    description="Query PostgreSQL for earthquake events, regional summaries, and monthly magnitude category breakdowns.",
)
def get_earthquake_visualization(
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    min_magnitude: Optional[float] = Query(None, ge=-1.0, le=10.0, description="Minimum magnitude threshold"),
    max_magnitude: Optional[float] = Query(None, ge=-1.0, le=10.0, description="Maximum magnitude threshold"),
    region: Optional[str] = Query(None, description="Geographical region filter name"),
    limit: int = Query(1000, gt=0, le=5000, description="Maximum event record count"),
    db: Session = Depends(get_db_session),
):
    """Fetch earthquake events and regional summaries from PostgreSQL."""
    data = VisualizationService.get_earthquake_visualization(
        session=db,
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
        max_magnitude=max_magnitude,
        region=region,
        limit=limit,
    )
    return EarthquakeVisualizationResponse(**data)


@router.get(
    "/analytics/trends",
    response_model=AnalyticsTrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Independent Timeseries Trends",
    description="Query PostgreSQL for independent daily PM2.5 averages and earthquake counts for trend analysis.",
)
def get_analytics_trends(
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db_session),
):
    """Fetch independent daily PM2.5 and earthquake time-series data."""
    data = VisualizationService.get_analytics_trends(
        session=db,
        start_date=start_date,
        end_date=end_date,
    )
    return AnalyticsTrendsResponse(**data)
