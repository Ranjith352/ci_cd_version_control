"""
Kafka Consumers for OpenAQ Air Quality and USGS Earthquakes.
"""

from .openaq_consumer import OpenAQConsumer
from .usgs_consumer import USGSConsumer
from .consumer_config import create_kafka_consumer, get_consumer_config

__all__ = [
    "OpenAQConsumer",
    "USGSConsumer",
    "create_kafka_consumer",
    "get_consumer_config",
]
