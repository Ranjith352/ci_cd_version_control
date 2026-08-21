import json
import unittest
from pathlib import Path
import pandas as pd
import numpy as np
from etl.transformation.openaq_transform import OpenAQTransformer, calculate_sub_aqi, PM25_BREAKPOINTS, PM10_BREAKPOINTS
from etl.transformation.usgs_transform import USGSTransformer, categorize_magnitude, extract_region_from_place

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class TestTransformations(unittest.TestCase):
    def setUp(self):
        with open(FIXTURES_DIR / "openaq_sample.json", "r", encoding="utf-8") as f:
            self.openaq_sample = json.load(f)
        with open(FIXTURES_DIR / "usgs_sample.json", "r", encoding="utf-8") as f:
            self.usgs_sample = json.load(f)

    def test_magnitude_categorization(self):
        self.assertEqual(categorize_magnitude(1.5), "Micro")
        self.assertEqual(categorize_magnitude(3.2), "Minor")
        self.assertEqual(categorize_magnitude(4.5), "Light")
        self.assertEqual(categorize_magnitude(5.8), "Moderate")
        self.assertEqual(categorize_magnitude(6.4), "Strong")
        self.assertEqual(categorize_magnitude(7.2), "Major")
        self.assertEqual(categorize_magnitude(8.5), "Great")
        self.assertEqual(categorize_magnitude(np.nan), "Unknown")

    def test_region_extraction(self):
        self.assertEqual(extract_region_from_place("12 km W of Cobb, CA"), "California, USA")
        self.assertEqual(extract_region_from_place("52 km SE of Hiroo, Japan"), "Hiroo, Japan")
        self.assertEqual(extract_region_from_place("Southern Alaska"), "Southern Alaska")
        self.assertEqual(extract_region_from_place(None), "Unknown Region")

    def test_aqi_calculation(self):
        self.assertEqual(calculate_sub_aqi(12.0, PM25_BREAKPOINTS), 50)
        self.assertEqual(calculate_sub_aqi(0.0, PM25_BREAKPOINTS), 0)
        self.assertEqual(calculate_sub_aqi(54.0, PM10_BREAKPOINTS), 50)
        self.assertIsNone(calculate_sub_aqi(-5.0, PM25_BREAKPOINTS))

    def test_openaq_transformer_pipeline(self):
        transformer = OpenAQTransformer()
        flat_df = transformer.extract_flat_records(self.openaq_sample)
        self.assertEqual(len(flat_df), 2)

        clean_df = transformer.transform(flat_df)
        self.assertEqual(len(clean_df), 2)
        self.assertIn("normalized_value", clean_df.columns)
        self.assertIn("aqi_us_epa", clean_df.columns)

        # Verify NO2 ppm unit conversion to µg/m³
        no2_row = clean_df[clean_df["parameter"] == "no2"].iloc[0]
        self.assertEqual(no2_row["normalized_unit"], "µg/m³")
        self.assertAlmostEqual(no2_row["normalized_value"], 0.05 * 1880.0, places=2)

    def test_usgs_transform_deduplication(self):
        transformer = USGSTransformer()
        sample_df = pd.DataFrame([
            {
                "event_id": "us1000a",
                "event_time_epoch_ms": 1700000000000,
                "magnitude": 4.5,
                "magnitude_type": "mb",
                "place": "California, USA",
                "longitude": -120.5,
                "latitude": 36.2,
                "depth_km": 10.0,
                "status": "reviewed",
                "event_type": "earthquake",
                "tsunami": 0,
                "event_url": "http://example.com/a",
            },
            {
                "event_id": "us1000a",  # Duplicate event_id
                "event_time_epoch_ms": 1700000000000,
                "magnitude": 4.5,
                "magnitude_type": "mb",
                "place": "California, USA",
                "longitude": -120.5,
                "latitude": 36.2,
                "depth_km": 10.0,
                "status": "reviewed",
                "event_type": "earthquake",
                "tsunami": 0,
                "event_url": "http://example.com/a",
            }
        ])

        clean_df = transformer.transform(sample_df)
        self.assertEqual(len(clean_df), 1)
        self.assertEqual(clean_df.iloc[0]["event_id"], "us1000a")
        self.assertEqual(clean_df.iloc[0]["magnitude_category"], "Light")

    def test_usgs_out_of_bounds_coordinates_dropped(self):
        transformer = USGSTransformer()
        invalid_coords_df = pd.DataFrame([
            {
                "event_id": "us_invalid_coords",
                "event_time_epoch_ms": 1700000000000,
                "magnitude": 4.5,
                "magnitude_type": "mb",
                "place": "Invalid",
                "longitude": -195.0,  # Out of bounds (< -180)
                "latitude": 36.2,
                "depth_km": 10.0,
                "status": "reviewed",
                "event_type": "earthquake",
                "tsunami": 0,
                "event_url": "http://example.com/inv",
            }
        ])
        clean_df = transformer.transform(invalid_coords_df)
        self.assertEqual(len(clean_df), 0)


if __name__ == "__main__":
    unittest.main()
