"""
Kafka Producer for USGS Earthquakes Real-Time Data.

Polls USGS GeoJSON API, formats events into EarthquakeMessage JSON,
deduplicates in-memory by event_id, and publishes to 'earthquakes-live'.
"""

import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from etl.extraction.usgs_extract import USGSExtractor
from kafka.producer.producer_config import create_kafka_producer
from kafka.schemas.earthquake import EarthquakeMessage, validate_earthquake_message
from kafka.utils.kafka_utils import TOPIC_EARTHQUAKES

logger = logging.getLogger(__name__)

USGS_POLL_INTERVAL = int(os.getenv("USGS_POLL_INTERVAL", "30"))
MAX_SEEN_IDS = 10000


class USGSProducer:
    """Producer service polling USGS GeoJSON API and pushing live earthquake events to Kafka."""

    def __init__(
        self,
        kafka_producer=None,
        extractor: Optional[USGSExtractor] = None,
        poll_interval: int = USGS_POLL_INTERVAL,
        topic_name: str = TOPIC_EARTHQUAKES,
    ):
        self.topic_name = topic_name
        self.poll_interval = poll_interval
        self.seen_event_ids: Set[str] = set()

        try:
            self.producer = kafka_producer if kafka_producer is not None else create_kafka_producer()
        except Exception as e:
            logger.warning("KafkaProducer initialization failed (%s). Operating in standalone/dry-run mode.", e)
            self.producer = None

        try:
            self.extractor = extractor if extractor is not None else USGSExtractor()
        except Exception as e:
            logger.warning("USGSExtractor initialization failed (%s).", e)
            self.extractor = None

    def create_message_from_feature(self, feature: Dict[str, Any]) -> Optional[EarthquakeMessage]:
        """Convert raw USGS GeoJSON feature into EarthquakeMessage."""
        event_id = feature.get("id")
        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or [0.0, 0.0, 0.0]

        if not event_id or len(coordinates) < 2:
            return None

        lon, lat = coordinates[0], coordinates[1]
        depth = coordinates[2] if len(coordinates) > 2 else 0.0
        mag = props.get("mag") or 0.0

        time_ms = props.get("time")
        if time_ms:
            event_time = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc).isoformat()
        else:
            event_time = datetime.now(timezone.utc).isoformat()

        place = props.get("place") or "Unknown place"
        parts = place.split(" of ")
        region = parts[-1].strip() if len(parts) > 1 else place

        # Categorize magnitude
        if mag < 3.0:
            category = "Minor"
        elif mag < 5.0:
            category = "Light"
        elif mag < 6.0:
            category = "Moderate"
        elif mag < 7.0:
            category = "Strong"
        elif mag < 8.0:
            category = "Major"
        else:
            category = "Great"

        try:
            msg = EarthquakeMessage(
                event_id=str(event_id),
                event_time=event_time,
                magnitude=float(mag),
                magnitude_type=props.get("magType") or "mb",
                place=place,
                region=region,
                longitude=float(lon),
                latitude=float(lat),
                depth_km=float(depth),
                magnitude_category=category,
                status=props.get("status") or "reviewed",
                event_type=props.get("type") or "earthquake",
                tsunami=int(props.get("tsunami") or 0),
                event_url=props.get("url") or "",
                source="usgs",
            )
            return msg
        except Exception as e:
            logger.error("Failed to parse EarthquakeMessage from GeoJSON feature: %s", e)
            return None

    def poll_and_publish_once(self, min_magnitude: float = 2.5) -> int:
        """
        Perform a single poll cycle: fetch USGS earthquakes, deduplicate, validate, publish.

        Returns:
            Number of new earthquake events published.
        """
        logger.info("Polling USGS earthquakes for topic '%s'...", self.topic_name)
        if not self.extractor:
            logger.error("No USGSExtractor configured. Skipping poll cycle.")
            return 0

        # Query recent events (past 1 hour / day)
        now_dt = datetime.now(timezone.utc)
        start_date = now_dt.strftime("%Y-%m-%d")

        try:
            raw_data = self.extractor.extract_earthquakes(
                start_date=start_date,
                min_magnitude=min_magnitude,
                limit=100,
            )
            geojson = raw_data.get("geojson") or {}
            features = geojson.get("features", [])
            logger.info("Discovered %d USGS earthquake events.", len(features))
        except Exception as e:
            logger.error("API Failure querying USGS API: %s", e)
            return 0

        published_count = 0
        duplicate_count = 0

        for feature in features:
            msg_obj = self.create_message_from_feature(feature)
            if not msg_obj:
                continue

            msg_dict = msg_obj.to_dict()
            event_id = msg_dict["event_id"]

            # Deduplication check
            if event_id in self.seen_event_ids:
                duplicate_count += 1
                continue

            # Schema validation check
            is_valid, reason = validate_earthquake_message(msg_dict)
            if not is_valid:
                logger.warning("Rejecting malformed earthquake event %s: %s", event_id, reason)
                continue

            # Publish to Kafka topic
            if self.producer is not None:
                try:
                    future = self.producer.send(
                        topic=self.topic_name,
                        key=str(event_id),
                        value=msg_dict,
                    )
                    record_metadata = future.get(timeout=5)
                    logger.debug(
                        "Published earthquake to %s [partition %d @ offset %d]",
                        record_metadata.topic,
                        record_metadata.partition,
                        record_metadata.offset,
                    )
                except Exception as e:
                    logger.error("Kafka send failed for event_id %s: %s", event_id, e)
                    continue

            # Mark seen & update counter
            self.seen_event_ids.add(event_id)
            published_count += 1

        # Maintain bounded deduplication set size
        if len(self.seen_event_ids) > MAX_SEEN_IDS:
            self.seen_event_ids = set(list(self.seen_event_ids)[-MAX_SEEN_IDS // 2 :])

        logger.info(
            "USGS Poll Cycle Complete: Published=%d, Duplicates Skipped=%d, Discovered=%d",
            published_count,
            duplicate_count,
            len(features),
        )
        return published_count

    def start_polling_loop(self, max_polls: Optional[int] = None):
        """Run continuous polling loop with configured interval."""
        logger.info("Starting USGS Kafka Producer polling loop (Interval: %ds)...", self.poll_interval)
        polls_completed = 0
        try:
            while max_polls is None or polls_completed < max_polls:
                self.poll_and_publish_once()
                polls_completed += 1
                if max_polls is None or polls_completed < max_polls:
                    time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("USGS Producer polling loop interrupted by user.")
        finally:
            if self.producer:
                self.producer.flush()
                logger.info("KafkaProducer flushed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    producer = USGSProducer()
    producer.poll_and_publish_once()
