from typing import List, Optional
from pydantic import BaseModel, Field


# 1. Air Quality Visualization Schemas
class AirQualitySummaryData(BaseModel):
    date: str = Field(..., description="Observation date (YYYY-MM-DD)")
    avg_concentration: float = Field(..., description="Daily average normalized concentration (µg/m³)")
    max_aqi: Optional[int] = Field(None, description="Maximum US EPA AQI sub-index calculated")


class AirQualityVisualizationResponse(BaseModel):
    city: str = Field(..., description="Query target city name")
    parameter: str = Field(..., description="Pollutant parameter (e.g. pm25, pm10, no2)")
    total_records: int = Field(..., description="Total aggregated daily data points")
    data: List[AirQualitySummaryData] = Field(default_factory=list, description="Aggregated daily concentration array")


# 2. Earthquake Visualization Schemas
class EarthquakeEventItem(BaseModel):
    event_id: str = Field(..., description="Unique USGS event ID")
    event_time: str = Field(..., description="UTC ISO timestamp of event")
    magnitude: float = Field(..., description="Richter magnitude value")
    magnitude_category: str = Field(..., description="Analytical category (Micro, Minor, Light, Moderate, etc.)")
    place: Optional[str] = Field(None, description="Relative location description")
    region: Optional[str] = Field(None, description="Extracted geographical region name")
    latitude: float = Field(..., description="Epicenter latitude (-90 to 90)")
    longitude: float = Field(..., description="Epicenter longitude (-180 to 180)")
    depth_km: float = Field(..., description="Hypocenter depth in kilometers")
    tsunami: int = Field(0, description="Tsunami alert flag (0 or 1)")


class RegionalSummaryItem(BaseModel):
    region: str = Field(..., description="Geographical region tag")
    total_events: int = Field(..., description="Event count in region")
    max_magnitude: float = Field(..., description="Maximum magnitude recorded")
    avg_depth_km: float = Field(..., description="Average depth in kilometers")
    tsunami_alerts: int = Field(..., description="Total tsunami alerts issued")


class MonthlyCategoryItem(BaseModel):
    month: str = Field(..., description="Year-month (YYYY-MM)")
    magnitude_category: str = Field(..., description="Magnitude analytical tier")
    event_count: int = Field(..., description="Number of quakes in category")


class EarthquakeVisualizationResponse(BaseModel):
    total_events: int = Field(..., description="Total seismic events returned")
    min_magnitude: float = Field(..., description="Minimum magnitude in set")
    max_magnitude: float = Field(..., description="Maximum magnitude in set")
    events: List[EarthquakeEventItem] = Field(default_factory=list, description="Seismic event details list")
    regional_summary: List[RegionalSummaryItem] = Field(default_factory=list, description="Regional aggregation breakdown")
    monthly_categories: List[MonthlyCategoryItem] = Field(default_factory=list, description="Monthly category breakdown")


# 3. Analytics / Trends Schemas
class TrendDataPoint(BaseModel):
    date: str = Field(..., description="Observation date (YYYY-MM-DD)")
    pm25_avg: Optional[float] = Field(None, description="Daily average PM2.5 concentration (µg/m³)")
    earthquake_count: int = Field(0, description="Daily total earthquake occurrences")


class AnalyticsTrendsResponse(BaseModel):
    total_days: int = Field(..., description="Number of days covered in trend range")
    trends: List[TrendDataPoint] = Field(default_factory=list, description="Independent daily timeseries data points")
