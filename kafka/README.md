# Real-Time Kafka Streaming Layer

This directory contains the complete **Phase 7 Real-Time Kafka & Redis Streaming Architecture** for the Environmental Intelligence Pipeline.

## Architecture

```
  OpenAQ / USGS APIs
         │
         ▼
  Kafka Producer (openaq_producer.py, usgs_producer.py)
         │
         ▼
  Kafka Topics (air-quality-live, earthquakes-live, + DLQ)
         │
         ▼
  Kafka Consumer (openaq_consumer.py, usgs_consumer.py)
         │
         ▼
  Fast Real-Time Store (Redis)
         │
         ▼
  FastAPI WebSocket & Endpoints (/api/live/*)
         │
         ▼
  React Live Dashboard (/live)
```

## Kafka Topics & Configurations

| Topic Name | Purpose | Partitions | Replication | Consumer Group |
|---|---|---|---|---|
| `air-quality-live` | Real-time OpenAQ measurements | 1 | 1 | `environmental-air-quality-consumer` |
| `earthquakes-live` | Newly detected USGS earthquake events | 1 | 1 | `environmental-earthquake-consumer` |
| `air-quality-live-dlq` | Dead-letter queue for invalid air quality messages | 1 | 1 | — |
| `earthquakes-live-dlq` | Dead-letter queue for invalid earthquake messages | 1 | 1 | — |

## Producer Deduplication & Reliability

- **Producer Settings**: `acks=all`, `retries=3`, `max_in_flight_requests_per_connection=1`.
- **Deduplication Strategy**: Logical in-memory tracking of `seen_measurement_ids` and `seen_event_ids` to prevent redundant message publishing during repeated API poll cycles.
- **Resilience**: Malformed API responses or temporary network errors are logged and skipped without crashing the producer.

## Consumer Processing & DLQ Strategy

- **Validation**: Incoming messages are strictly validated against required fields and coordinate/value ranges before persisting.
- **Storage**: Valid messages are written to Redis (`air_quality:latest:<id>`, `earthquake:latest:<id>`) and prepended to bounded recent lists (`air_quality:recent`, `earthquake:recent`).
- **Dead-Letter Queue (DLQ)**: Malformed or unprocessable payloads are routed to `*-dlq` topics with failure timestamp, error reason, and preserved original payload.
- **Offset Management**: Kafka offsets are committed manually only after successful storage or DLQ routing.

## Local Execution Guide

### 1. Topic Initialization
```bash
python kafka/setup_topics.py
```

### 2. Start Producers
```bash
python kafka/producer/openaq_producer.py
python kafka/producer/usgs_producer.py
```

### 3. Start Consumers
```bash
python kafka/consumer/openaq_consumer.py
python kafka/consumer/usgs_consumer.py
```
