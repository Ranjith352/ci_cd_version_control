import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from etl.extraction.usgs_extract import USGSExtractor

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class TestUSGSExtract(unittest.TestCase):
    def setUp(self):
        with open(FIXTURES_DIR / "usgs_sample.json", "r", encoding="utf-8") as f:
            self.sample_data = json.load(f)

    @patch("requests.get")
    def test_usgs_extract_earthquakes_mocked(self, mock_get):
        """Verify USGS earthquake extraction using mocked HTTP GeoJSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_data["geojson"]
        mock_get.return_value = mock_response

        extractor = USGSExtractor()
        raw_data = extractor.extract_earthquakes(
            start_date="2026-01-01",
            end_date="2026-08-20",
            min_magnitude=2.5,
            limit=1000
        )

        self.assertIn("metadata", raw_data)
        self.assertIn("geojson", raw_data)
        geojson = raw_data["geojson"]
        self.assertEqual(geojson.get("type"), "FeatureCollection")

        features = geojson.get("features", [])
        self.assertEqual(len(features), 2)

        first_feat = features[0]
        self.assertEqual(first_feat["id"], "us7000m123")
        self.assertIn("properties", first_feat)
        self.assertIn("geometry", first_feat)

        props = first_feat["properties"]
        expected_props = ["mag", "place", "time", "magType", "status", "type", "tsunami", "url"]
        for p in expected_props:
            self.assertIn(p, props, f"Missing property {p} in USGS earthquake feature")

        self.assertTrue(mock_get.called)

    @patch("requests.get")
    def test_usgs_extract_malformed_json_raises_value_error(self, mock_get):
        """Verify malformed GeoJSON JSONDecodeError raises ValueError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
        mock_get.return_value = mock_response

        extractor = USGSExtractor()
        with self.assertRaises(ValueError):
            extractor.extract_earthquakes(start_date="2026-01-01")


if __name__ == "__main__":
    unittest.main()
