"""
Kafka Real-Time Streaming Module for Environmental Intelligence Pipeline.
Includes dynamic delegation to installed third-party kafka-python library.
"""

import sys
import os
import importlib

__version__ = "1.0.0"

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)


def _load_tp_kafka_module(submodule: str = None):
    _sys_path_backup = list(sys.path)
    try:
        sys.path = [p for p in sys.path if os.path.abspath(p) not in (_parent_dir, _current_dir, "")]
        if submodule:
            return importlib.import_module(f"kafka.{submodule}")
        return importlib.import_module("kafka")
    finally:
        sys.path = _sys_path_backup


try:
    _tp_kafka = _load_tp_kafka_module()
    KafkaProducer = getattr(_tp_kafka, "KafkaProducer", None)
    KafkaConsumer = getattr(_tp_kafka, "KafkaConsumer", None)
    KafkaAdminClient = getattr(_tp_kafka, "KafkaAdminClient", None)
except Exception:
    KafkaProducer = None
    KafkaConsumer = None
    KafkaAdminClient = None


def __getattr__(name: str):
    """Dynamically fall back to installed kafka-python package submodules/attributes."""
    try:
        return _load_tp_kafka_module(name)
    except Exception:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
