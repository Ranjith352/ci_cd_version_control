"""
Kafka and Redis Utility Functions.
"""

from .kafka_utils import (
    KAFKA_BOOTSTRAP_SERVERS,
    TOPIC_AIR_QUALITY,
    TOPIC_EARTHQUAKES,
    TOPIC_AIR_QUALITY_DLQ,
    TOPIC_EARTHQUAKES_DLQ,
    json_serializer,
    json_deserializer,
    check_kafka_health,
)
from .redis_client import RealTimeStore, get_redis_client

__all__ = [
    "KAFKA_BOOTSTRAP_SERVERS",
    "TOPIC_AIR_QUALITY",
    "TOPIC_EARTHQUAKES",
    "TOPIC_AIR_QUALITY_DLQ",
    "TOPIC_EARTHQUAKES_DLQ",
    "json_serializer",
    "json_deserializer",
    "check_kafka_health",
    "RealTimeStore",
    "get_redis_client",
]
