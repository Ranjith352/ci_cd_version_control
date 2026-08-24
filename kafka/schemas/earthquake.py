"""
Earthquake Message Schema definition and validation logic for 'earthquakes-live' Kafka topic.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Tuple


REQUIRED_EARTHQUAKE_FIELDS = [
    "event_id",
    "event_time",
    "magnitude",
    "latitude",
    "longitude",
    "depth_km",
]


class EarthquakeMessage:
    """Class representation of real-time USGS earthquake events."""

    def __init__(
        self,
        event_id: str,
        event_time: str,
        magnitude: float,
        latitude: float,
        longitude: float,
        depth_km: float,
        magnitude_type: str = "mb",
        place: str = "Unknown location",
        region: str = "Global",
        magnitude_category: str = "Minor",
        status: str = "reviewed",
        event_type: str = "earthquake",
        tsunami: int = 0,
        event_url: str = "",
        source: str = "usgs",
        published_at: str = None,
    ):
        self.event_id = str(event_id)
        self.event_time = event_time
        self.magnitude = float(magnitude)
        self.magnitude_type = magnitude_type
        self.place = place
        self.region = region
        self.longitude = float(longitude)
        self.latitude = float(latitude)
        self.depth_km = float(depth_km)
        self.magnitude_category = magnitude_category
        self.status = status
        self.event_type = event_type
        self.tsunami = int(tsunami)
        self.event_url = event_url
        self.source = source
        self.published_at = published_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message instance to serializable dictionary."""
        return {
            "event_id": self.event_id,
            "event_time": self.event_time,
            "magnitude": self.magnitude,
            "magnitude_type": self.magnitude_type,
            "place": self.place,
            "region": self.region,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "depth_km": self.depth_km,
            "magnitude_category": self.magnitude_category,
            "status": self.status,
            "event_type": self.event_type,
            "tsunami": self.tsunami,
            "event_url": self.event_url,
            "source": self.source,
            "published_at": self.published_at,
        }


def validate_earthquake_message(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate incoming dictionary against Earthquake message schema.

    Returns:
        (is_valid, error_reason)
    """
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"

    for field in REQUIRED_EARTHQUAKE_FIELDS:
        if field not in data or data[field] is None:
            return False, f"Missing required field: '{field}'"

    # Numeric validations
    try:
        float(data["magnitude"])
        float(data["latitude"])
        float(data["longitude"])
        float(data["depth_km"])
    except (ValueError, TypeError):
        return False, "Fields 'magnitude', 'latitude', 'longitude', and 'depth_km' must be numeric"

    # Latitude / Longitude boundary validation
    lat = float(data["latitude"])
    lon = float(data["longitude"])
    if not (-90 <= lat <= 90):
        return False, f"Latitude {lat} out of range [-90, 90]"
    if not (-180 <= lon <= 180):
        return False, f"Longitude {lon} out of range [-180, 180]"

    return True, ""
