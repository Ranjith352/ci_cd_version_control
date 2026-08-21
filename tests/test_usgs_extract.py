import unittest
from etl.extraction.usgs_extract import USGSExtractor

class TestUSGSExtract(unittest.TestCase):
    def test_usgs_extract_live_or_structure(self):
        extractor = USGSExtractor()
        raw_data = extractor.extract_earthquakes(
            start_date="2026-01-01",
            end_date="2026-01-05",
            min_magnitude=4.5,
            limit=5
        )

        self.assertIn("metadata", raw_data)
        self.assertIn("geojson", raw_data)
        geojson = raw_data["geojson"]
        self.assertEqual(geojson.get("type"), "FeatureCollection")
        
        features = geojson.get("features", [])
        self.assertGreater(len(features), 0)

        first_feat = features[0]
        self.assertIn("id", first_feat)
        self.assertIn("properties", first_feat)
        self.assertIn("geometry", first_feat)
        
        props = first_feat["properties"]
        expected_props = ["mag", "place", "time", "magType", "status", "type", "tsunami", "url"]
        for p in expected_props:
            self.assertIn(p, props, f"Missing property {p} in USGS earthquake feature")

if __name__ == "__main__":
    unittest.main()
