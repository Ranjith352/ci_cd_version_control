import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.database.repository import (
    AirQualityRepository,
    EarthquakeRepository,
    AnalyticsRepository,
)

logger = logging.getLogger("backend.services.visualization")


class VisualizationService:
    """Service formatting database aggregations for React frontend visualizations."""

    @staticmethod
    def get_air_quality_visualization(
        session: Session,
        city: str = "Coimbatore",
        parameter: str = "pm25",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch daily air quality concentration averages and max AQI."""
        daily_records = AirQualityRepository.get_daily_summary(
            session=session,
            city=city,
            parameter=parameter,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "city": city,
            "parameter": parameter.lower(),
            "total_records": len(daily_records),
            "data": daily_records,
        }

    @staticmethod
    def get_earthquake_visualization(
        session: Session,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_magnitude: Optional[float] = None,
        max_magnitude: Optional[float] = None,
        region: Optional[str] = None,
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """Fetch earthquake events list, regional summaries, and monthly magnitude category breakdowns."""
        events = EarthquakeRepository.get_events(
            session=session,
            start_date=start_date,
            end_date=end_date,
            min_magnitude=min_magnitude,
            max_magnitude=max_magnitude,
            region=region,
            limit=limit,
        )

        mags = [e["magnitude"] for e in events] if events else [0.0]
        min_mag = min(mags) if events else (min_magnitude or 0.0)
        max_mag = max(mags) if events else (max_magnitude or 0.0)

        regional_summary = EarthquakeRepository.get_regional_summary(session=session)
        monthly_categories = EarthquakeRepository.get_monthly_categories(session=session)

        return {
            "total_events": len(events),
            "min_magnitude": round(float(min_mag), 2),
            "max_magnitude": round(float(max_mag), 2),
            "events": events,
            "regional_summary": regional_summary,
            "monthly_categories": monthly_categories,
        }

    @staticmethod
    def get_analytics_trends(
        session: Session,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch independent daily PM2.5 averages and earthquake counts for trend analysis."""
        trend_records = AnalyticsRepository.get_independent_trends(
            session=session,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "total_days": len(trend_records),
            "trends": trend_records,
        }
