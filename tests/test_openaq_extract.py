import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from etl.extraction.openaq_extract import OpenAQExtractor

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class TestOpenAQExtract(unittest.TestCase):
    def setUp(self):
        with open(FIXTURES_DIR / "openaq_sample.json", "r", encoding="utf-8") as f:
            self.sample_data = json.load(f)

    def test_openaq_extractor_initialization_with_key(self):
        extractor = OpenAQExtractor(api_key="test_key_12345")
        self.assertEqual(extractor.api_key, "test_key_12345")
        self.assertEqual(extractor.headers.get("X-API-Key"), "test_key_12345")

    def test_openaq_extractor_missing_key_raises_error(self):
        with patch.dict("os.environ", {"OPENAQ_API_KEY": ""}, clear=True):
            with self.assertRaises(ValueError):
                OpenAQExtractor(api_key="")

    @patch("requests.get")
    def test_openaq_extract_location_data_mocked(self, mock_get):
        """Verify OpenAQ extraction process using mocked API responses."""
        # 1. Mock locations response
        mock_loc_response = MagicMock()
        mock_loc_response.status_code = 200
        mock_loc_response.json.return_value = {
            "results": self.sample_data["locations"],
            "meta": {"found": 1}
        }

        # 2. Mock sensors response
        mock_sensors_response = MagicMock()
        mock_sensors_response.status_code = 200
        mock_sensors_response.json.return_value = {
            "results": self.sample_data["sensors"],
            "meta": {"found": 2}
        }

        # 3. Mock measurements response
        mock_meas_response = MagicMock()
        mock_meas_response.status_code = 200
        mock_meas_response.json.return_value = {
            "results": self.sample_data["measurements"],
            "meta": {"found": 2}
        }

        # Set side effect for sequence of requests: locations -> sensors -> measurements
        mock_get.side_effect = [
            mock_loc_response,
            mock_sensors_response,
            mock_meas_response,
            mock_meas_response,
        ]

        extractor = OpenAQExtractor(api_key="test_mock_key")
        result = extractor.extract_location_data(city="Coimbatore")

        self.assertIn("metadata", result)
        self.assertIn("measurements", result)
        self.assertEqual(len(result["locations"]), 1)
        self.assertGreaterEqual(len(result["measurements"]), 1)
        self.assertTrue(mock_get.called)

    @patch("requests.get")
    def test_openaq_http_401_unauthorized_raises_runtime_error(self, mock_get):
        """Verify HTTP 401 raises explicit RuntimeError without silent swallowing."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        extractor = OpenAQExtractor(api_key="invalid_key")
        with self.assertRaises(RuntimeError):
            extractor.fetch_locations(city="Coimbatore")


if __name__ == "__main__":
    unittest.main()
