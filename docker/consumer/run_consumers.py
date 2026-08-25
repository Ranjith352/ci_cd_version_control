"""
Daemon runner executing continuous consumption loops for OpenAQ and USGS Kafka Consumers inside Docker container.
"""

import os
import sys
import time
import logging
import signal
import threading

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kafka.consumer.openaq_consumer import OpenAQConsumer
from kafka.consumer.usgs_consumer import USGSConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("kafka_consumer_daemon")

running = True


def handle_shutdown(signum, frame):
    global running
    logger.info("Received shutdown signal (%s). Exiting consumer daemon...", signum)
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def run_openaq_consumer():
    logger.info("Initializing OpenAQ Consumer...")
    consumer = None
    while running and consumer is None:
        try:
            consumer = OpenAQConsumer()
            logger.info("OpenAQ Consumer initialized successfully!")
        except Exception as e:
            logger.warning("Waiting for Kafka/Redis connection (%s)... retrying in 5 seconds", e)
            time.sleep(5)

    while running:
        try:
            consumer.consume_batch(max_messages=20)
        except Exception as e:
            logger.error("Error in OpenAQ Consumer loop: %s", e)
        time.sleep(1.0)


def run_usgs_consumer():
    logger.info("Initializing USGS Consumer...")
    consumer = None
    while running and consumer is None:
        try:
            consumer = USGSConsumer()
            logger.info("USGS Consumer initialized successfully!")
        except Exception as e:
            logger.warning("Waiting for Kafka/Redis connection (%s)... retrying in 5 seconds", e)
            time.sleep(5)

    while running:
        try:
            consumer.consume_batch(max_messages=20)
        except Exception as e:
            logger.error("Error in USGS Consumer loop: %s", e)
        time.sleep(1.0)


def main():
    logger.info("Starting OpenAQ & USGS Kafka Consumer Daemon threads...")

    t1 = threading.Thread(target=run_openaq_consumer, daemon=True)
    t2 = threading.Thread(target=run_usgs_consumer, daemon=True)

    t1.start()
    t2.start()

    while running:
        time.sleep(1.0)

    logger.info("Kafka Consumer Daemon shut down cleanly.")


if __name__ == "__main__":
    main()
