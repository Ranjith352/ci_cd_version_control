"""
Unit tests for OpenAQ and USGS Kafka Producers (mocked).
"""

from unittest.mock import MagicMock
from kafka.producer.openaq_producer import OpenAQProducer
from kafka.producer.usgs_producer import USGSProducer


def test_openaq_producer_deduplication():
    mock_kafka = MagicMock()
    mock_extractor = MagicMock()

    # Return 2 records with identical measurement_id
    mock_extractor.extract_location_data.return_value = {
        "measurements": [
            {
                "measurement_id": 9991,
                "location_id": 8914,
                "location_name": "Coimbatore Station",
                "city": "Coimbatore",
                "country": "IN",
                "parameter": "pm25",
                "value": 18.5,
                "unit": "µg/m³",
                "latitude": 11.0168,
                "longitude": 76.9558,
                "datetime_utc": "2026-08-24T12:00:00Z",
            },
            {
                "measurement_id": 9991,  # Duplicate
                "location_id": 8914,
                "location_name": "Coimbatore Station",
                "city": "Coimbatore",
                "country": "IN",
                "parameter": "pm25",
                "value": 18.5,
                "unit": "µg/m³",
                "latitude": 11.0168,
                "longitude": 76.9558,
                "datetime_utc": "2026-08-24T12:00:00Z",
            },
        ]
    }

    producer = OpenAQProducer(kafka_producer=mock_kafka, extractor=mock_extractor)
    published = producer.poll_and_publish_once(city="Coimbatore")

    # Should only publish 1 due to deduplication
    assert published == 1
    assert mock_kafka.send.call_count == 1
    assert 9991 in producer.seen_measurement_ids


def test_usgs_producer_deduplication():
    mock_kafka = MagicMock()
    mock_extractor = MagicMock()

    # Return 2 identical USGS features
    mock_extractor.extract_earthquakes.return_value = {
        "geojson": {
            "features": [
                {
                    "id": "us7000test",
                    "properties": {"mag": 4.5, "place": "Tokyo, Japan", "time": 1700000000000},
                    "geometry": {"coordinates": [139.69, 35.68, 10.0]},
                },
                {
                    "id": "us7000test",  # Duplicate
                    "properties": {"mag": 4.5, "place": "Tokyo, Japan", "time": 1700000000000},
                    "geometry": {"coordinates": [139.69, 35.68, 10.0]},
                },
            ]
        }
    }

    producer = USGSProducer(kafka_producer=mock_kafka, extractor=mock_extractor)
    published = producer.poll_and_publish_once()

    assert published == 1
    assert mock_kafka.send.call_count == 1
    assert "us7000test" in producer.seen_event_ids
