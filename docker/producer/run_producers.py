"""
Daemon runner executing continuous polling cycles for OpenAQ and USGS Kafka Producers inside Docker container.
"""

import os
import sys
import time
import logging
import signal

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kafka.producer.openaq_producer import OpenAQProducer
from kafka.producer.usgs_producer import USGSProducer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("kafka_producer_daemon")

running = True


def handle_shutdown(signum, frame):
    global running
    logger.info("Received shutdown signal (%s). Exiting producer daemon...", signum)
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def main():
    logger.info("Initializing OpenAQ & USGS Kafka Producer Daemon...")
    
    openaq_producer = None
    usgs_producer = None
    
    # Retry initialization until Kafka broker is reachable
    while running and (openaq_producer is None or usgs_producer is None):
        try:
            if openaq_producer is None:
                openaq_producer = OpenAQProducer()
            if usgs_producer is None:
                usgs_producer = USGSProducer()
            logger.info("Kafka Producers successfully initialized!")
        except Exception as e:
            logger.warning("Waiting for Kafka broker connection (%s)... retrying in 5 seconds", e)
            time.sleep(5)

    openaq_interval = int(os.getenv("OPENAQ_POLL_INTERVAL", "30"))
    usgs_interval = int(os.getenv("USGS_POLL_INTERVAL", "30"))
    poll_step = 5
    elapsed_openaq = openaq_interval  # Trigger immediately on startup
    elapsed_usgs = usgs_interval

    logger.info(
        "Starting producer polling loop (OpenAQ interval: %ds, USGS interval: %ds)...",
        openaq_interval,
        usgs_interval,
    )

    while running:
        if elapsed_openaq >= openaq_interval:
            try:
                count_aq = openaq_producer.poll_and_publish_once(city="Coimbatore")
                logger.info("OpenAQ poll completed: %d records published.", count_aq)
            except Exception as e:
                logger.error("Error during OpenAQ poll cycle: %s", e)
            elapsed_openaq = 0

        if elapsed_usgs >= usgs_interval:
            try:
                count_usgs = usgs_producer.poll_and_publish_once(min_magnitude=1.0)
                logger.info("USGS poll completed: %d events published.", count_usgs)
            except Exception as e:
                logger.error("Error during USGS poll cycle: %s", e)
            elapsed_usgs = 0

        time.sleep(poll_step)
        elapsed_openaq += poll_step
        elapsed_usgs += poll_step

    logger.info("Kafka Producer Daemon shut down cleanly.")


if __name__ == "__main__":
    main()
