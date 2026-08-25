"""
Kafka Producer for OpenAQ Air Quality Real-Time Data.

Polls OpenAQ API, formats measurements into AirQualityMessage JSON,
deduplicates in-memory by measurement_id, and publishes to 'air-quality-live'.
"""

import logging
import os
import time
from typing import Any, Dict, Optional, Set

from etl.extraction.openaq_extract import OpenAQExtractor
from kafka.producer.producer_config import create_kafka_producer
from kafka.schemas.air_quality import AirQualityMessage, validate_air_quality_message
from kafka.utils.kafka_utils import TOPIC_AIR_QUALITY

logger = logging.getLogger(__name__)

OPENAQ_POLL_INTERVAL = int(os.getenv("OPENAQ_POLL_INTERVAL", "30"))
MAX_SEEN_IDS = 10000


class OpenAQProducer:
    """Producer service polling OpenAQ and pushing live events to Kafka."""

    def __init__(
        self,
        kafka_producer=None,
        extractor: Optional[OpenAQExtractor] = None,
        poll_interval: int = OPENAQ_POLL_INTERVAL,
        topic_name: str = TOPIC_AIR_QUALITY,
    ):
        self.topic_name = topic_name
        self.poll_interval = poll_interval
        self.seen_measurement_ids: Set[Any] = set()

        try:
            self.producer = kafka_producer if kafka_producer is not None else create_kafka_producer()
        except Exception as e:
            logger.warning("KafkaProducer initialization failed (%s). Operating in standalone/dry-run mode.", e)
            self.producer = None

        try:
            self.extractor = extractor if extractor is not None else OpenAQExtractor()
        except Exception as e:
            logger.warning("OpenAQExtractor initialization failed (%s).", e)
            self.extractor = None

    def create_message_from_record(self, record: Dict[str, Any], index: int = 1) -> Optional[AirQualityMessage]:
        """Convert extracted OpenAQ record dictionary into structured AirQualityMessage."""
        dt = record.get("datetime_utc") or record.get("datetime_local")
        if not dt:
            dt = "2026-08-24T12:00:00Z"

        # Unique measurement ID generation or retrieval
        meas_id = record.get("measurement_id") or record.get("id")
        if not meas_id:
            loc_id = record.get("location_id", 8914)
            param = record.get("parameter", "pm25")
            val = record.get("value", 0)
            meas_id = f"openaq_{loc_id}_{param}_{dt}_{val}_{index}"

        try:
            msg = AirQualityMessage(
                measurement_id=meas_id,
                location_id=record.get("location_id", 8914),
                location_name=record.get("location_name", "Coimbatore Station"),
                city=record.get("city", "Coimbatore"),
                country=record.get("country", "IN"),
                latitude=record.get("latitude", 11.0168),
                longitude=record.get("longitude", 76.9558),
                parameter=record.get("parameter", "pm25"),
                value=record.get("value", 0.0),
                unit=record.get("unit", "µg/m³"),
                normalized_value=record.get("value", 0.0),
                normalized_unit=record.get("unit", "µg/m³"),
                aqi_us_epa=record.get("aqi_us_epa"),
                reading_timestamp=str(dt),
                source="openaq",
            )
            return msg
        except Exception as e:
            logger.error("Failed to construct AirQualityMessage from record: %s", e)
            return None

    def poll_and_publish_once(self, city: str = "Coimbatore") -> int:
        """
        Perform a single poll cycle: fetch OpenAQ data, deduplicate, validate, publish.

        Returns:
            Number of new records successfully published.
        """
        logger.info("Polling OpenAQ measurements for topic '%s'...", self.topic_name)
        if not self.extractor:
            logger.error("No OpenAQExtractor configured. Skipping poll cycle.")
            return 0

        try:
            raw_data = self.extractor.extract_location_data(city=city)
            records = raw_data.get("measurements", [])
            logger.info("Discovered %d OpenAQ measurement records.", len(records))
        except Exception as e:
            logger.error("Error polling OpenAQ API: %s", e)
            return 0

        published_count = 0
        duplicate_count = 0

        for idx, rec in enumerate(records, start=1):
            msg_obj = self.create_message_from_record(rec, index=idx)
            if not msg_obj:
                continue

            msg_dict = msg_obj.to_dict()
            meas_id = msg_dict["measurement_id"]

            # Deduplication check
            if meas_id in self.seen_measurement_ids:
                duplicate_count += 1
                continue

            # Schema validation check
            is_valid, reason = validate_air_quality_message(msg_dict)
            if not is_valid:
                logger.warning("Rejecting invalid measurement %s: %s", meas_id, reason)
                continue

            # Publish to Kafka topic
            if self.producer is not None:
                try:
                    future = self.producer.send(
                        topic=self.topic_name,
                        key=str(meas_id),
                        value=msg_dict,
                    )
                    # Block briefly for metadata delivery confirmation
                    record_metadata = future.get(timeout=5)
                    logger.debug(
                        "Published to %s [partition %d @ offset %d]",
                        record_metadata.topic,
                        record_metadata.partition,
                        record_metadata.offset,
                    )
                except Exception as e:
                    logger.error("Kafka send failed for measurement_id %s: %s", meas_id, e)
                    continue

            # Mark seen & update counter
            self.seen_measurement_ids.add(meas_id)
            published_count += 1

        # Maintain bounded size for in-memory deduplication set
        if len(self.seen_measurement_ids) > MAX_SEEN_IDS:
            self.seen_measurement_ids = set(list(self.seen_measurement_ids)[-MAX_SEEN_IDS // 2 :])

        logger.info(
            "OpenAQ Poll Cycle Complete: Published=%d, Duplicates Skipped=%d, Total Discovered=%d",
            published_count,
            duplicate_count,
            len(records),
        )
        return published_count

    def start_polling_loop(self, max_polls: Optional[int] = None):
        """Run continuous polling loop with configured interval."""
        logger.info("Starting OpenAQ Kafka Producer polling loop (Interval: %ds)...", self.poll_interval)
        polls_completed = 0
        try:
            while max_polls is None or polls_completed < max_polls:
                self.poll_and_publish_once()
                polls_completed += 1
                if max_polls is None or polls_completed < max_polls:
                    time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("OpenAQ Producer polling loop interrupted by user.")
        finally:
            if self.producer:
                self.producer.flush()
                logger.info("KafkaProducer flushed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    producer = OpenAQProducer()
    producer.poll_and_publish_once()
