"""
Kafka Consumer Configuration and Factory.
"""

import logging
from typing import Any, Dict

from kafka import KafkaConsumer

from kafka.utils.kafka_utils import KAFKA_BOOTSTRAP_SERVERS, json_deserializer

logger = logging.getLogger(__name__)


def get_consumer_config(group_id: str) -> Dict[str, Any]:
    """Get consumer configuration dictionary for given consumer group."""
    return {
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
        "group_id": group_id,
        "auto_offset_reset": "earliest",
        "enable_auto_commit": False,
        "value_deserializer": json_deserializer,
        "key_deserializer": lambda k: k.decode("utf-8") if k is not None else None,
        "consumer_timeout_ms": 1000,
    }


def create_kafka_consumer(topic_name: str, group_id: str, config: Dict[str, Any] = None) -> KafkaConsumer:
    """
    Instantiate KafkaConsumer subscribed to topic_name.

    Raises:
        Exception: If connection or setup fails.
    """
    cfg = config or get_consumer_config(group_id)
    try:
        consumer = KafkaConsumer(topic_name, **cfg)
        logger.info(
            "KafkaConsumer initialized for topic '%s' in consumer group '%s'",
            topic_name,
            group_id,
        )
        return consumer
    except Exception as e:
        logger.error("Failed to initialize KafkaConsumer for '%s': %s", topic_name, e)
        raise
