"""
Redis Fast Real-Time Store Helper for Environmental Intelligence Pipeline.

Provides connection management, storage, retrieval, and bounded retention policies.
Falls back safely to an in-memory store if Redis is unavailable or unconfigured.
"""

import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_MAX_ITEMS = int(os.getenv("REDIS_MAX_ITEMS", "100"))

_redis_client_instance = None
_in_memory_store = {
    "air_quality_latest": {},
    "air_quality_recent": [],
    "earthquake_latest": {},
    "earthquake_recent": [],
}


def get_redis_client():
    """Get or initialize Redis client instance."""
    global _redis_client_instance
    if _redis_client_instance is not None:
        return _redis_client_instance

    try:
        import redis
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection ping
        client.ping()
        _redis_client_instance = client
        logger.info("Successfully connected to Redis at %s", REDIS_URL)
        return _redis_client_instance
    except Exception as e:
        logger.warning("Redis connection unavailable (%s). Falling back to in-memory store.", e)
        return None


class RealTimeStore:
    """High-level real-time storage interface wrapping Redis with in-memory fallback."""

    def __init__(self, redis_client=None):
        self.client = redis_client if redis_client is not None else get_redis_client()

    def is_healthy(self) -> bool:
        """Check connection health."""
        if self.client is not None:
            try:
                return bool(self.client.ping())
            except Exception:
                return False
        # If fallback mode active, treat store as healthy in-memory fallback
        return True

    # ------------------------------------------------------------------
    # AIR QUALITY METHODS
    # ------------------------------------------------------------------
    def save_air_quality(self, data: Dict[str, Any]) -> bool:
        """Store latest air quality measurement and append to recent collection."""
        meas_id = str(data.get("measurement_id"))
        key = f"air_quality:latest:{meas_id}"
        serialized = json.dumps(data)

        if self.client is not None:
            try:
                # Save latest key with TTL (e.g. 86400s / 24 hours)
                self.client.set(key, serialized, ex=86400)
                # Push to recent list & trim
                self.client.lpush("air_quality:recent", serialized)
                self.client.ltrim("air_quality:recent", 0, REDIS_MAX_ITEMS - 1)
                return True
            except Exception as e:
                logger.error("Error writing air quality to Redis: %s", e)

        # Fallback in-memory
        _in_memory_store["air_quality_latest"][meas_id] = data
        _in_memory_store["air_quality_recent"].insert(0, data)
        if len(_in_memory_store["air_quality_recent"]) > REDIS_MAX_ITEMS:
            _in_memory_store["air_quality_recent"] = _in_memory_store["air_quality_recent"][:REDIS_MAX_ITEMS]
        return True

    def get_recent_air_quality(self, count: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent air quality measurements."""
        if self.client is not None:
            try:
                items = self.client.lrange("air_quality:recent", 0, count - 1)
                return [json.loads(item) for item in items if item]
            except Exception as e:
                logger.error("Error reading air quality from Redis: %s", e)

        # Fallback in-memory
        return _in_memory_store["air_quality_recent"][:count]

    # ------------------------------------------------------------------
    # EARTHQUAKE METHODS
    # ------------------------------------------------------------------
    def save_earthquake(self, data: Dict[str, Any]) -> bool:
        """Store latest earthquake event and append to recent collection."""
        event_id = str(data.get("event_id"))
        key = f"earthquake:latest:{event_id}"
        serialized = json.dumps(data)

        if self.client is not None:
            try:
                # Save latest key with 24h TTL
                self.client.set(key, serialized, ex=86400)
                # Push to recent list & trim
                self.client.lpush("earthquake:recent", serialized)
                self.client.ltrim("earthquake:recent", 0, REDIS_MAX_ITEMS - 1)
                return True
            except Exception as e:
                logger.error("Error writing earthquake to Redis: %s", e)

        # Fallback in-memory
        _in_memory_store["earthquake_latest"][event_id] = data
        _in_memory_store["earthquake_recent"].insert(0, data)
        if len(_in_memory_store["earthquake_recent"]) > REDIS_MAX_ITEMS:
            _in_memory_store["earthquake_recent"] = _in_memory_store["earthquake_recent"][:REDIS_MAX_ITEMS]
        return True

    def get_recent_earthquakes(self, count: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent earthquake events."""
        if self.client is not None:
            try:
                items = self.client.lrange("earthquake:recent", 0, count - 1)
                return [json.loads(item) for item in items if item]
            except Exception as e:
                logger.error("Error reading earthquakes from Redis: %s", e)

        # Fallback in-memory
        return _in_memory_store["earthquake_recent"][:count]
