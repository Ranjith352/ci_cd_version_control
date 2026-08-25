"""
Kafka Consumer for OpenAQ Air Quality Real-Time Data.

Subscribes to 'air-quality-live', validates messages, stores latest/recent records
in Redis, routes malformed records to DLQ 'air-quality-live-dlq', and commits offsets.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from kafka.consumer.consumer_config import create_kafka_consumer
from kafka.schemas.air_quality import validate_air_quality_message
from kafka.utils.kafka_utils import TOPIC_AIR_QUALITY, TOPIC_AIR_QUALITY_DLQ
from kafka.utils.redis_client import RealTimeStore

logger = logging.getLogger(__name__)

GROUP_ID_AIR_QUALITY = "environmental-air-quality-consumer"


class OpenAQConsumer:
    """Consumer service processing live air quality messages."""

    def __init__(
        self,
        kafka_consumer=None,
        kafka_producer=None,
        store: Optional[RealTimeStore] = None,
        topic_name: str = TOPIC_AIR_QUALITY,
        dlq_topic: str = TOPIC_AIR_QUALITY_DLQ,
        group_id: str = GROUP_ID_AIR_QUALITY,
    ):
        self.topic_name = topic_name
        self.dlq_topic = dlq_topic
        self.group_id = group_id
        self.store = store or RealTimeStore()

        try:
            self.consumer = kafka_consumer if kafka_consumer is not None else create_kafka_consumer(
                topic_name=self.topic_name,
                group_id=self.group_id,
            )
        except Exception as e:
            logger.warning("KafkaConsumer unavailable (%s). Consumer running in mock mode.", e)
            self.consumer = None

        self.producer = kafka_producer

    def push_to_dlq(self, payload: Any, error_reason: str):
        """Publish malformed or unprocessable payload to DLQ topic."""
        dlq_event = {
            "original_payload": payload,
            "error_reason": error_reason,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "consumer_group": self.group_id,
        }
        logger.warning("Routing message to DLQ [%s]: %s", self.dlq_topic, error_reason)

        if self.producer is not None:
            try:
                self.producer.send(self.dlq_topic, value=dlq_event)
                self.producer.flush()
            except Exception as e:
                logger.error("Failed to publish to DLQ topic %s: %s", self.dlq_topic, e)

    def process_message(self, message_val: Any) -> bool:
        """
        Validate, store, and process single air quality message.

        Returns:
            True if successfully processed or safely routed to DLQ.
        """
        if not isinstance(message_val, dict):
            self.push_to_dlq(message_val, "Invalid message type, expected JSON object")
            return True

        is_valid, reason = validate_air_quality_message(message_val)
        if not is_valid:
            self.push_to_dlq(message_val, f"Validation failure: {reason}")
            return True

        # Store in Redis / fast real-time store
        try:
            stored = self.store.save_air_quality(message_val)
            if stored:
                logger.info(
                    "Successfully processed & stored Air Quality reading for measurement_id=%s (location_id=%s)",
                    message_val.get("measurement_id"),
                    message_val.get("location_id"),
                )
                return True
            else:
                logger.error("Failed to store Air Quality reading in real-time store.")
                return False
        except Exception as e:
            logger.error("Error storing Air Quality reading in real-time store: %s", e)
            return False

    def consume_batch(self, max_messages: int = 10) -> int:
        """Poll and process up to max_messages from Kafka topic."""
        if not self.consumer:
            logger.debug("No active Kafka consumer. Skipping consume step.")
            return 0

        processed_count = 0
        try:
            records = self.consumer.poll(timeout_ms=1000, max_records=max_messages)
            for topic_partition, msgs in records.items():
                for msg in msgs:
                    success = self.process_message(msg.value)
                    if success:
                        processed_count += 1

            if processed_count > 0:
                self.consumer.commit()
                logger.info("Committed offset after processing %d records.", processed_count)

        except Exception as e:
            logger.error("Error during OpenAQ consumer poll batch: %s", e)

        return processed_count

    def start_consumer_loop(self):
        """Run continuous consumption loop."""
        logger.info("Starting OpenAQ Consumer loop for topic '%s'...", self.topic_name)
        try:
            while True:
                self.consume_batch()
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("OpenAQ Consumer loop stopped by user.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    consumer = OpenAQConsumer()
    consumer.consume_batch()
