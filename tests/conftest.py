import json
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from etl.loading.load import initialize_schema

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


@pytest.fixture
def openaq_raw_sample():
    """Load deterministic OpenAQ sample raw JSON fixture."""
    fixture_file = FIXTURES_DIR / "openaq_sample.json"
    with open(fixture_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def usgs_raw_sample():
    """Load deterministic USGS sample raw GeoJSON fixture."""
    fixture_file = FIXTURES_DIR / "usgs_sample.json"
    with open(fixture_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sqlite_test_engine():
    """Create isolated in-memory SQLite database engine initialized with DDL schema."""
    engine = create_engine("sqlite:///:memory:")
    initialize_schema(engine, db_type="sqlite")
    return engine
