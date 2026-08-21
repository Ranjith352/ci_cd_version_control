import unittest
import pandas as pd
import numpy as np
from etl.transformation.openaq_transform import OpenAQTransformer, calculate_sub_aqi, PM25_BREAKPOINTS
from etl.transformation.usgs_transform import USGSTransformer, categorize_magnitude, extract_region_from_place

class TestTransformations(unittest.TestCase):
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

    def test_aqi_calculation(self):
        self.assertEqual(calculate_sub_aqi(12.0, PM25_BREAKPOINTS), 50)
        self.assertEqual(calculate_sub_aqi(0.0, PM25_BREAKPOINTS), 0)
        self.assertIsNone(calculate_sub_aqi(-5.0, PM25_BREAKPOINTS))

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
        self.assertEqual(clean_df.iloc[0]["event_time"], "2023-11-14T22:13:20Z")

if __name__ == "__main__":
    unittest.main()
