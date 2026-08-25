"""
Kafka utilities for connection checking, topic status, and health reporting.
"""

import json
import logging
import os
import sys
import importlib
import threading
from typing import Any

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")

TOPIC_AIR_QUALITY = "air-quality-live"
TOPIC_EARTHQUAKES = "earthquakes-live"
TOPIC_AIR_QUALITY_DLQ = "air-quality-live-dlq"
TOPIC_EARTHQUAKES_DLQ = "earthquakes-live-dlq"

_tp_kafka_lock = threading.Lock()
_tp_kafka_module = None


def json_serializer(obj: Any) -> bytes:
    """Serialize object or dict into UTF-8 JSON bytes."""
    return json.dumps(obj, default=str).encode("utf-8")


def json_deserializer(bytes_data: bytes) -> Any:
    """Deserialize UTF-8 JSON bytes into Python object."""
    if not bytes_data:
        return None
    return json.loads(bytes_data.decode("utf-8"))


def _get_third_party_kafka():
    """Thread-safely import and cache the third-party kafka package from site-packages."""
    global _tp_kafka_module
    if _tp_kafka_module is not None:
        return _tp_kafka_module

    with _tp_kafka_lock:
        if _tp_kafka_module is not None:
            return _tp_kafka_module

        _current_dir = os.path.normcase(os.path.abspath(os.path.dirname(__file__)))
        _parent_dir = os.path.normcase(os.path.abspath(os.path.join(_current_dir, "../..")))

        _old_sys_path = list(sys.path)
        _clean_sys_path = [
            p for p in sys.path
            if os.path.normcase(os.path.abspath(p)) not in (_parent_dir, _current_dir, "")
        ]

        _saved_kafka_modules = {
            k: v for k, v in sys.modules.items()
            if k == "kafka" or k.startswith("kafka.")
        }
        for k in list(_saved_kafka_modules.keys()):
            sys.modules.pop(k, None)

        try:
            sys.path = _clean_sys_path
            tp_mod = importlib.import_module("kafka")
            _tp_kafka_module = tp_mod
        finally:
            sys.path = _old_sys_path
            # Restore project modules into sys.modules
            sys.modules.update(_saved_kafka_modules)

        return _tp_kafka_module


def _import_tp_kafka_class(class_name: str, *args, **kwargs):
    """Instantiate third-party kafka class cleanly without module collision."""
    tp_kafka = _get_third_party_kafka()
    cls = getattr(tp_kafka, class_name)
    if args or kwargs:
        return cls(*args, **kwargs)
    return cls


def get_kafka_producer(*args, **kwargs):
    return _import_tp_kafka_class("KafkaProducer", *args, **kwargs)


def get_kafka_consumer(*args, **kwargs):
    return _import_tp_kafka_class("KafkaConsumer", *args, **kwargs)


def get_kafka_admin_client(*args, **kwargs):
    return _import_tp_kafka_class("KafkaAdminClient", *args, **kwargs)


def check_kafka_health(bootstrap_servers: str = None) -> bool:
    """
    Check connection health to Kafka broker.

    Returns:
        True if broker responds, False otherwise.
    """
    servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
    try:
        admin = get_kafka_admin_client(
            bootstrap_servers=servers,
            api_version=(0, 10, 2),
            request_timeout_ms=3000,
        )
        topics = admin.list_topics()
        admin.close()
        logger.info("Kafka cluster responsive. Active topics: %s", topics)
        return True
    except Exception as e:
        logger.warning("Kafka broker health check failed (%s)", e)
        return False
