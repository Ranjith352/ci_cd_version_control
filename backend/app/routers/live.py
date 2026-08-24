"""
FastAPI Real-Time API Router for Live Kafka/Redis Environmental Streaming Layer.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from kafka.utils.kafka_utils import check_kafka_health
from kafka.utils.redis_client import RealTimeStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live", tags=["Real-Time Streaming Layer"])
store = RealTimeStore()


@router.get("/air-quality", response_model=Dict[str, Any])
def get_live_air_quality(count: int = 20):
    """Fetch latest real-time OpenAQ air quality measurements populated by Kafka consumer."""
    records = store.get_recent_air_quality(count=count)
    return {
        "source": "kafka",
        "count": len(records),
        "records": records,
    }


@router.get("/earthquakes", response_model=Dict[str, Any])
def get_live_earthquakes(count: int = 20):
    """Fetch latest real-time USGS earthquake events populated by Kafka consumer."""
    events = store.get_recent_earthquakes(count=count)
    return {
        "source": "kafka",
        "count": len(events),
        "events": events,
    }


@router.get("/health", response_model=Dict[str, Any])
def get_live_health():
    """Check connectivity health for Kafka broker and Redis store."""
    redis_healthy = store.is_healthy()
    kafka_healthy = check_kafka_health()

    status_code = 200 if (redis_healthy or kafka_healthy) else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "kafka": "healthy" if kafka_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
        },
    )


@router.websocket("/ws")
async def websocket_live_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint streaming live environmental events to connected React clients.
    """
    await websocket.accept()
    logger.info("WebSocket connection established with client: %s", websocket.client)

    last_aq_id = None
    last_eq_id = None

    try:
        # Send initial snapshot
        initial_aq = store.get_recent_air_quality(count=5)
        initial_eq = store.get_recent_earthquakes(count=5)

        await websocket.send_json({
            "type": "SNAPSHOT",
            "air_quality": initial_aq,
            "earthquakes": initial_eq,
        })

        if initial_aq:
            last_aq_id = initial_aq[0].get("measurement_id")
        if initial_eq:
            last_eq_id = initial_eq[0].get("event_id")

        while True:
            await asyncio.sleep(2)

            recent_aq = store.get_recent_air_quality(count=5)
            recent_eq = store.get_recent_earthquakes(count=5)

            new_aq = []
            if recent_aq:
                current_top_aq = recent_aq[0].get("measurement_id")
                if current_top_aq != last_aq_id:
                    new_aq = recent_aq
                    last_aq_id = current_top_aq

            new_eq = []
            if recent_eq:
                current_top_eq = recent_eq[0].get("event_id")
                if current_top_eq != last_eq_id:
                    new_eq = recent_eq
                    last_eq_id = current_top_eq

            if new_aq or new_eq:
                await websocket.send_json({
                    "type": "UPDATE",
                    "air_quality": new_aq,
                    "earthquakes": new_eq,
                })
            else:
                # Send periodic heartbeat to keep connection alive
                await websocket.send_json({"type": "HEARTBEAT"})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected gracefully.")
    except Exception as e:
        logger.error("WebSocket streaming error: %s", e)
        try:
            await websocket.close()
        except Exception:
            pass
