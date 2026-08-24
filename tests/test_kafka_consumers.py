"""
Unit tests for OpenAQ and USGS Kafka Consumers (mocked).
"""

from unittest.mock import MagicMock
from kafka.consumer.openaq_consumer import OpenAQConsumer
from kafka.consumer.usgs_consumer import USGSConsumer


def test_openaq_consumer_valid_message():
    mock_store = MagicMock()
    mock_store.save_air_quality.return_value = True

    consumer = OpenAQConsumer(kafka_consumer=None, store=mock_store)

    valid_payload = {
        "measurement_id": 1001,
        "location_id": 8914,
        "parameter": "pm25",
        "value": 15.2,
        "latitude": 11.0168,
        "longitude": 76.9558,
        "reading_timestamp": "2026-08-24T12:00:00Z",
    }

    success = consumer.process_message(valid_payload)
    assert success is True
    mock_store.save_air_quality.assert_called_once_with(valid_payload)


def test_openaq_consumer_malformed_message_routes_to_dlq():
    mock_store = MagicMock()
    mock_producer = MagicMock()

    consumer = OpenAQConsumer(kafka_consumer=None, kafka_producer=mock_producer, store=mock_store)

    malformed_payload = {
        "measurement_id": 1001,
        # Missing required parameter and coordinates
    }

    success = consumer.process_message(malformed_payload)
    assert success is True
    # Store should not be called for malformed payload
    mock_store.save_air_quality.assert_not_called()
    # Producer should publish to DLQ
    assert mock_producer.send.call_count == 1
    dlq_topic = mock_producer.send.call_args[0][0]
    assert dlq_topic == "air-quality-live-dlq"


def test_usgs_consumer_valid_message():
    mock_store = MagicMock()
    mock_store.save_earthquake.return_value = True

    consumer = USGSConsumer(kafka_consumer=None, store=mock_store)

    valid_payload = {
        "event_id": "us7000valid",
        "event_time": "2026-08-24T12:00:00Z",
        "magnitude": 5.1,
        "latitude": 35.68,
        "longitude": 139.69,
        "depth_km": 10.0,
        "place": "Tokyo, Japan",
    }

    success = consumer.process_message(valid_payload)
    assert success is True
    mock_store.save_earthquake.assert_called_once_with(valid_payload)


def test_usgs_consumer_malformed_routes_to_dlq():
    mock_store = MagicMock()
    mock_producer = MagicMock()

    consumer = USGSConsumer(kafka_consumer=None, kafka_producer=mock_producer, store=mock_store)

    malformed_payload = "NOT_A_DICTIONARY"

    success = consumer.process_message(malformed_payload)
    assert success is True
    mock_store.save_earthquake.assert_not_called()
    assert mock_producer.send.call_count == 1
    dlq_topic = mock_producer.send.call_args[0][0]
    assert dlq_topic == "earthquakes-live-dlq"
