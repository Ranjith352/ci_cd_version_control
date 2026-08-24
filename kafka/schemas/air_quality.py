"""
Air Quality Message Schema definition and validation logic for 'air-quality-live' Kafka topic.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Tuple


REQUIRED_AIR_QUALITY_FIELDS = [
    "measurement_id",
    "location_id",
    "parameter",
    "value",
    "latitude",
    "longitude",
    "reading_timestamp",
]


class AirQualityMessage:
    """Class representation of real-time OpenAQ air quality measurements."""

    def __init__(
        self,
        measurement_id: int | str,
        location_id: int | str,
        parameter: str,
        value: float,
        latitude: float,
        longitude: float,
        reading_timestamp: str,
        location_name: str = "Unknown Location",
        city: str = "Unknown",
        country: str = "Unknown",
        unit: str = "µg/m³",
        normalized_value: float = None,
        normalized_unit: str = "µg/m³",
        aqi_us_epa: int = None,
        source: str = "openaq",
        published_at: str = None,
    ):
        self.measurement_id = measurement_id
        self.location_id = location_id
        self.location_name = location_name
        self.city = city
        self.country = country
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.parameter = parameter
        self.value = float(value)
        self.unit = unit
        self.normalized_value = float(normalized_value) if normalized_value is not None else float(value)
        self.normalized_unit = normalized_unit
        self.aqi_us_epa = int(aqi_us_epa) if aqi_us_epa is not None else None
        self.reading_timestamp = reading_timestamp
        self.source = source
        self.published_at = published_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message instance to serializable dictionary."""
        return {
            "measurement_id": self.measurement_id,
            "location_id": self.location_id,
            "location_name": self.location_name,
            "city": self.city,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "parameter": self.parameter,
            "value": self.value,
            "unit": self.unit,
            "normalized_value": self.normalized_value,
            "normalized_unit": self.normalized_unit,
            "aqi_us_epa": self.aqi_us_epa,
            "reading_timestamp": self.reading_timestamp,
            "source": self.source,
            "published_at": self.published_at,
        }


def validate_air_quality_message(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate incoming dictionary against Air Quality message schema.

    Returns:
        (is_valid, error_reason)
    """
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"

    for field in REQUIRED_AIR_QUALITY_FIELDS:
        if field not in data or data[field] is None:
            return False, f"Missing required field: '{field}'"

    # Numeric validations
    try:
        float(data["value"])
        float(data["latitude"])
        float(data["longitude"])
    except (ValueError, TypeError):
        return False, "Fields 'value', 'latitude', and 'longitude' must be numeric"

    # Latitude / Longitude boundary validation
    lat = float(data["latitude"])
    lon = float(data["longitude"])
    if not (-90 <= lat <= 90):
        return False, f"Latitude {lat} out of range [-90, 90]"
    if not (-180 <= lon <= 180):
        return False, f"Longitude {lon} out of range [-180, 180]"

    return True, ""
