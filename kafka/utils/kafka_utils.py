"""
Kafka utilities for connection checking, topic status, and health reporting.
"""

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

TOPIC_AIR_QUALITY = "air-quality-live"
TOPIC_EARTHQUAKES = "earthquakes-live"
TOPIC_AIR_QUALITY_DLQ = "air-quality-live-dlq"
TOPIC_EARTHQUAKES_DLQ = "earthquakes-live-dlq"


def json_serializer(obj: Any) -> bytes:
    """Serialize object or dict into UTF-8 JSON bytes."""
    return json.dumps(obj, default=str).encode("utf-8")


def json_deserializer(bytes_data: bytes) -> Any:
    """Deserialize UTF-8 JSON bytes into Python object."""
    if not bytes_data:
        return None
    return json.loads(bytes_data.decode("utf-8"))


def check_kafka_health(bootstrap_servers: str = None) -> bool:
    """
    Check connection health to Kafka broker.

    Returns:
        True if broker responds, False otherwise.
    """
    servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
    try:
        from kafka import KafkaAdminClient
        admin = KafkaAdminClient(
            bootstrap_servers=servers,
            request_timeout_ms=3000,
        )
        topics = admin.list_topics()
        admin.close()
        logger.info("Kafka cluster responsive. Active topics: %s", topics)
        return True
    except Exception as e:
        logger.warning("Kafka broker health check failed (%s)", e)
        return False
