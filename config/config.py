import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# Load environment variables explicitly from project root .env
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

RAW_OPENAQ_DIR = DATA_RAW_DIR / "openaq"
RAW_USGS_DIR = DATA_RAW_DIR / "usgs"
PROCESSED_OPENAQ_DIR = DATA_PROCESSED_DIR / "openaq"
PROCESSED_USGS_DIR = DATA_PROCESSED_DIR / "usgs"
DATABASE_DIR = PROJECT_ROOT / "database"

# Ensure directories exist
for path in [RAW_OPENAQ_DIR, RAW_USGS_DIR, PROCESSED_OPENAQ_DIR, PROCESSED_USGS_DIR, DATABASE_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# API Configurations
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY", "").strip()
OPENAQ_BASE_URL = os.getenv("OPENAQ_BASE_URL", "https://api.openaq.org/v3").rstrip("/")
USGS_API_URL = os.getenv("USGS_API_URL", "https://earthquake.usgs.gov/fdsnws/event/1/query").strip()

# Database Configurations
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "environmental_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Construct SQLAlchemy database URL
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


def get_masked_api_key(key: str = None) -> str:
    """Return a masked version of the API key for secure logging."""
    target_key = key if key is not None else OPENAQ_API_KEY
    if not target_key:
        return "<NOT_SET>"
    if len(target_key) <= 8:
        return "********"
    return f"{target_key[:4]}...{target_key[-4:]}"


def validate_config():
    """Validate core configurations and issue warnings if keys are missing."""
    if not OPENAQ_API_KEY:
        print("[WARNING] OPENAQ_API_KEY is missing in .env file.")
        print("[INFO] OpenAQ v3 API requires an API key in the 'X-API-Key' header.")
        print("[INFO] You can obtain a free API key at https://openaq.org")
    else:
        print(f"[INFO] OpenAQ API key loaded: {get_masked_api_key()}")
    print(f"[INFO] USGS API URL: {USGS_API_URL}")
    print(f"[INFO] PostgreSQL Host: {POSTGRES_HOST}:{POSTGRES_PORT}, DB: {POSTGRES_DB}")


if __name__ == "__main__":
    validate_config()
