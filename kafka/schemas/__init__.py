"""
JSON Message Schemas and Validation for Kafka Topics.
"""

from .air_quality import AirQualityMessage, validate_air_quality_message
from .earthquake import EarthquakeMessage, validate_earthquake_message

__all__ = [
    "AirQualityMessage",
    "validate_air_quality_message",
    "EarthquakeMessage",
    "validate_earthquake_message",
]
