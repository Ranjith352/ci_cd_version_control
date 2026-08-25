"""
Kafka Producer Configuration and Factory.
"""

import logging
import os
from typing import Any, Dict

from kafka.utils.kafka_utils import (
    KAFKA_BOOTSTRAP_SERVERS,
    get_kafka_producer,
    json_serializer,
)

logger = logging.getLogger(__name__)


def get_producer_config() -> Dict[str, Any]:
    """Get default producer configuration dict."""
    retries = int(os.getenv("KAFKA_RETRIES", "3"))
    return {
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
        "acks": "all",
        "retries": retries,
        "max_in_flight_requests_per_connection": 1,
        "value_serializer": json_serializer,
        "key_serializer": lambda k: str(k).encode("utf-8") if k is not None else None,
        "request_timeout_ms": 10000,
    }


def create_kafka_producer(config: Dict[str, Any] = None):
    """
    Instantiate KafkaProducer client.

    Raises:
        KafkaError: If connection or configuration fails.
    """
    cfg = config or get_producer_config()
    try:
        producer = get_kafka_producer(**cfg)
        logger.info("KafkaProducer successfully initialized connecting to %s", cfg.get("bootstrap_servers"))
        return producer
    except Exception as e:
        logger.error("Failed to initialize KafkaProducer: %s", e)
        raise
