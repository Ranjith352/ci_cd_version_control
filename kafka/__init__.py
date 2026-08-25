"""
Kafka Real-Time Streaming Module for Environmental Intelligence Pipeline.
"""

import os

__version__ = "1.0.0"

_current_dir = os.path.normcase(os.path.abspath(os.path.dirname(__file__)))
_parent_dir = os.path.normcase(os.path.abspath(os.path.join(_current_dir, "..")))


def __getattr__(name: str):
    """
    Forward requests for third-party kafka symbols (e.g. KafkaConsumer, KafkaProducer, version, errors)
    to the installed third-party kafka package.
    """
    from kafka.utils.kafka_utils import _get_third_party_kafka

    tp_kafka = _get_third_party_kafka()
    if hasattr(tp_kafka, name):
        return getattr(tp_kafka, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

