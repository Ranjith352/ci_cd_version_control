import unittest
import pandas as pd
from sqlalchemy import create_engine, text
from etl.loading.load import initialize_schema, load_earthquakes_upsert

class TestLoading(unittest.TestCase):
    def setUp(self):
        """Create in-memory SQLite database for testing loading operations."""
        self.engine = create_engine("sqlite:///:memory:")
        initialize_schema(self.engine, db_type="sqlite")

    def test_earthquake_upsert_idempotency(self):
        sample_eq = pd.DataFrame([{
            "event_id": "test_eq_999",
            "event_time": "2026-08-20T10:00:00Z",
            "magnitude": 5.2,
            "magnitude_type": "mwb",
            "place": "Off Coast of Honshu, Japan",
            "region": "Japan",
            "longitude": 142.500000,
            "latitude": 38.200000,
            "depth_km": 25.40,
            "magnitude_category": "Moderate",
            "status": "reviewed",
            "event_type": "earthquake",
            "tsunami": 1,
            "event_url": "http://earthquake.usgs.gov/events/test_eq_999",
        }])

        # First load
        loaded1 = load_earthquakes_upsert(self.engine, sample_eq, db_type="sqlite")
        self.assertEqual(loaded1, 1)

        with self.engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM earthquake_events")).scalar()
            self.assertEqual(count, 1)

        # Second load with updated magnitude (upsert test)
        sample_eq_updated = sample_eq.copy()
        sample_eq_updated["magnitude"] = 5.5

        loaded2 = load_earthquakes_upsert(self.engine, sample_eq_updated, db_type="sqlite")
        self.assertEqual(loaded2, 1)

        with self.engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM earthquake_events")).scalar()
            self.assertEqual(count, 1)  # 0 duplicates created!
            
            mag = conn.execute(text("SELECT magnitude FROM earthquake_events WHERE event_id = 'test_eq_999'")).scalar()
            self.assertEqual(mag, 5.5)  # Record updated!

if __name__ == "__main__":
    unittest.main()
