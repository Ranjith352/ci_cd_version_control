"""
Idempotent topic initialization script for Kafka cluster.
Creates 'air-quality-live', 'earthquakes-live', 'air-quality-live-dlq', and 'earthquakes-live-dlq'.
"""

import logging
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kafka.utils.kafka_utils import (
    KAFKA_BOOTSTRAP_SERVERS,
    TOPIC_AIR_QUALITY,
    TOPIC_AIR_QUALITY_DLQ,
    TOPIC_EARTHQUAKES,
    TOPIC_EARTHQUAKES_DLQ,
    get_kafka_admin_client,
    _import_tp_kafka_class,
)

KafkaAdminClient = get_kafka_admin_client
NewTopic = _import_tp_kafka_class("admin").NewTopic
TopicAlreadyExistsError = _import_tp_kafka_class("errors").TopicAlreadyExistsError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def setup_kafka_topics(bootstrap_servers: str = None) -> bool:
    """
    Initialize required Kafka topics idempotently.

    Returns:
        True if all topics exist/were created, False if setup failed.
    """
    servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
    logger.info("Connecting to Kafka cluster at %s...", servers)

    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=servers,
            client_id="kafka-topic-initializer",
            request_timeout_ms=5000,
        )
    except Exception as e:
        logger.error("Failed to connect to Kafka Admin Client: %s", e)
        return False

    existing_topics = set(admin_client.list_topics())
    logger.info("Existing cluster topics: %s", list(existing_topics))

    target_topics = [
        NewTopic(name=TOPIC_AIR_QUALITY, num_partitions=1, replication_factor=1),
        NewTopic(name=TOPIC_EARTHQUAKES, num_partitions=1, replication_factor=1),
        NewTopic(name=TOPIC_AIR_QUALITY_DLQ, num_partitions=1, replication_factor=1),
        NewTopic(name=TOPIC_EARTHQUAKES_DLQ, num_partitions=1, replication_factor=1),
    ]

    topics_to_create = [t for t in target_topics if t.name not in existing_topics]

    if not topics_to_create:
        logger.info("All target Kafka topics already exist. No action needed.")
        admin_client.close()
        return True

    logger.info("Creating missing topics: %s", [t.name for t in topics_to_create])
    try:
        admin_client.create_topics(new_topics=topics_to_create, validate_only=False)
        logger.info("Successfully created Kafka topics.")
    except TopicAlreadyExistsError:
        logger.info("One or more topics already existed during creation.")
    except Exception as e:
        logger.error("Error creating Kafka topics: %s", e)
        admin_client.close()
        return False

    admin_client.close()
    return True


if __name__ == "__main__":
    success = setup_kafka_topics()
    sys.exit(0 if success else 1)
