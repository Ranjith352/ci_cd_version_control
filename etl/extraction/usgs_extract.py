import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import requests

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.config import RAW_USGS_DIR, USGS_API_URL

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class USGSExtractor:
    """Extractor for USGS Earthquake Hazards Program GeoJSON API."""

    def __init__(self, api_url: Optional[str] = None):
        self.api_url = (api_url or USGS_API_URL).rstrip("/")
        self.headers = {"User-Agent": "Environmental-Intelligence-Pipeline/1.0"}

    def extract_earthquakes(
        self,
        start_date: str = "2026-01-01",
        end_date: Optional[str] = None,
        min_magnitude: float = 2.5,
        max_magnitude: Optional[float] = None,
        min_latitude: Optional[float] = None,
        max_latitude: Optional[float] = None,
        min_longitude: Optional[float] = None,
        max_longitude: Optional[float] = None,
        limit: int = 1000,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Fetch earthquake events matching query criteria from USGS API."""
        if not end_date:
            end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        params = {
            "format": "geojson",
            "starttime": start_date,
            "endtime": end_date,
            "minmagnitude": min_magnitude,
            "limit": limit,
            "orderby": "time",
        }

        if max_magnitude is not None:
            params["maxmagnitude"] = max_magnitude
        if min_latitude is not None:
            params["minlatitude"] = min_latitude
        if max_latitude is not None:
            params["maxlatitude"] = max_latitude
        if min_longitude is not None:
            params["minlongitude"] = min_longitude
        if max_longitude is not None:
            params["maxlongitude"] = max_longitude

        logger.info(f"Querying USGS API: {self.api_url} with params: {params}")

        try:
            response = requests.get(self.api_url, headers=self.headers, params=params, timeout=timeout)
            response.raise_for_status()

            data = response.json()
            features = data.get("features", [])
            logger.info(f"Successfully retrieved {len(features)} earthquake events from USGS API.")

            # Attach extraction metadata wrapper
            raw_data = {
                "metadata": {
                    "extracted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "api_url": self.api_url,
                    "query_params": params,
                    "count": len(features),
                },
                "geojson": data,
            }
            return raw_data

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error querying USGS API ({response.status_code}): {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout querying USGS API: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error querying USGS API: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode GeoJSON response from USGS API: {e}")
            raise ValueError(f"Malformed GeoJSON returned by USGS API: {e}")

    def save_raw_json(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save raw USGS API response as JSON in data/raw/usgs/."""
        if not filename:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"usgs_raw_{timestamp}.json"

        file_path = RAW_USGS_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved raw USGS response to: {file_path}")
        return str(file_path)


def run_usgs_extraction(
    start_date: str = "2026-01-01",
    end_date: Optional[str] = None,
    min_magnitude: float = 2.5,
) -> str:
    """Entry point function to execute USGS earthquake data extraction."""
    extractor = USGSExtractor()
    raw_data = extractor.extract_earthquakes(
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
    )
    filepath = extractor.save_raw_json(raw_data)
    return filepath


if __name__ == "__main__":
    run_usgs_extraction()
