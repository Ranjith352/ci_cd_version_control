import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import requests
from dotenv import load_dotenv

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.config import (
    ENV_PATH,
    OPENAQ_BASE_URL,
    RAW_OPENAQ_DIR,
    get_masked_api_key,
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Configurable volume/pagination settings
OPENAQ_LIMIT = int(os.getenv("OPENAQ_LIMIT", "100"))
OPENAQ_MAX_PAGES = int(os.getenv("OPENAQ_MAX_PAGES", "2"))
OPENAQ_DATE_FROM = os.getenv("OPENAQ_DATE_FROM", "").strip()
OPENAQ_DATE_TO = os.getenv("OPENAQ_DATE_TO", "").strip()


class OpenAQExtractor:
    """Extractor for real OpenAQ v3 API data (Location -> Sensors -> Measurements)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        key_from_env = os.getenv("OPENAQ_API_KEY", "").strip()

        self.api_key = (api_key if api_key is not None else key_from_env).strip()
        self.base_url = (base_url or OPENAQ_BASE_URL).rstrip("/")
        self.headers = {"User-Agent": "Environmental-Intelligence-Pipeline/1.0"}

        if not self.api_key:
            logger.error(f"OPENAQ_API_KEY is missing or empty in .env at {ENV_PATH}")
            raise ValueError(
                f"No OPENAQ_API_KEY configured in {ENV_PATH}. "
                "OpenAQ v3 API requires an API key in the 'X-API-Key' header. "
                "Please set OPENAQ_API_KEY=<your_key> in your .env file."
            )

        self.headers["X-API-Key"] = self.api_key
        logger.info(f"Initialized OpenAQExtractor with API Key: {get_masked_api_key(self.api_key)}")

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Dict[str, Any]:
        """Make an HTTP GET request to OpenAQ API with strict error handling and resilience to 5xx server glitches."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            logger.info(f"Requesting OpenAQ URL: {url} with params: {params}")
            response = requests.get(url, headers=self.headers, params=params, timeout=timeout)

            if response.status_code == 401:
                logger.error(
                    f"HTTP 401 Unauthorized: OPENAQ_API_KEY in .env ({get_masked_api_key(self.api_key)}) "
                    "was rejected by OpenAQ API."
                )
                raise RuntimeError(
                    f"OpenAQ Authentication Failed (HTTP 401 Unauthorized). "
                    f"API key '{get_masked_api_key(self.api_key)}' is invalid or unauthorized."
                )
            elif response.status_code == 403:
                logger.error("HTTP 403 Forbidden: Restricted OpenAQ endpoint.")
                raise RuntimeError("OpenAQ API HTTP 403 Forbidden. Check your API key permissions.")
            elif response.status_code == 429:
                logger.warning("HTTP 429 Rate Limit Exceeded. Waiting 2 seconds...")
                time.sleep(2)
                response = requests.get(url, headers=self.headers, params=params, timeout=timeout)
            elif response.status_code == 404:
                logger.warning(f"HTTP 404 Not Found for OpenAQ endpoint: {url}")
                return {"results": [], "meta": {"found": 0}}
            elif response.status_code >= 500:
                logger.warning(f"HTTP {response.status_code} Server Error for OpenAQ URL: {url}")
                return {"results": [], "meta": {"found": 0}}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during OpenAQ API request: {e}")
            return {"results": [], "meta": {"found": 0}}
        except requests.exceptions.Timeout as e:
            logger.error(f"OpenAQ API request timed out ({timeout}s): {e}")
            return {"results": [], "meta": {"found": 0}}
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error contacting OpenAQ API: {e}")
            return {"results": [], "meta": {"found": 0}}

    def fetch_locations(
        self,
        city: Optional[str] = None,
        coordinates: Optional[tuple] = None,
        radius: int = 50000,
        country_code: Optional[str] = None,
        order_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        limit: int = 15,
        page: int = 1,
    ) -> Dict[str, Any]:
        """GET /v3/locations"""
        params = {"limit": limit, "page": page}

        if city:
            params["city"] = city
        elif coordinates and len(coordinates) == 2:
            lat, lon = coordinates
            params["coordinates"] = f"{lat},{lon}"
            params["radius"] = radius
        elif country_code:
            params["country_code"] = country_code

        if order_by:
            params["order_by"] = order_by
        if sort_order:
            params["sort_order"] = sort_order

        return self._make_request("locations", params=params)

    def fetch_location_sensors(self, location_id: int) -> List[Dict[str, Any]]:
        """GET /v3/locations/{location_id}/sensors"""
        endpoint = f"locations/{location_id}/sensors"
        try:
            res = self._make_request(endpoint)
            sensors = res.get("results", [])
            if not sensors:
                logger.info(f"No sensors found for location_id {location_id}.")
            return sensors
        except Exception as e:
            logger.warning(f"Failed to fetch sensors for location_id {location_id}: {e}")
            return []

    def fetch_sensor_measurements(
        self,
        sensor_id: int,
        limit: int = OPENAQ_LIMIT,
        max_pages: int = OPENAQ_MAX_PAGES,
        date_from: Optional[str] = OPENAQ_DATE_FROM,
        date_to: Optional[str] = OPENAQ_DATE_TO,
    ) -> List[Dict[str, Any]]:
        """GET /v3/sensors/{sensor_id}/measurements with pagination."""
        endpoint = f"sensors/{sensor_id}/measurements"
        all_measurements = []

        for page in range(1, max_pages + 1):
            params = {"limit": limit, "page": page}
            if date_from:
                params["datetime_from"] = date_from
            if date_to:
                params["datetime_to"] = date_to

            try:
                res = self._make_request(endpoint, params=params)
                meas = res.get("results", [])

                if not meas:
                    if page == 1:
                        logger.info(f"No measurements found for sensor_id {sensor_id}.")
                    break

                all_measurements.extend(meas)
                logger.info(f"Sensor_id {sensor_id} (Page {page}): Retrieved {len(meas)} measurements.")

                meta = res.get("meta", {})
                found_raw = meta.get("found", len(all_measurements))
                try:
                    found = int(str(found_raw).replace("+", "").strip())
                except ValueError:
                    found = len(all_measurements)

                if len(all_measurements) >= found or len(meas) < limit:
                    break
            except Exception as e:
                logger.warning(f"Error fetching measurements for sensor_id {sensor_id} page {page}: {e}")
                break

        return all_measurements

    def _extract_from_locations_list(self, locations: List[Dict[str, Any]]) -> tuple:
        """Helper to process a list of location objects into sensors and normalized measurements."""
        raw_sensors_metadata = []
        normalized_records = []

        for loc in locations:
            loc_id = loc.get("id")
            loc_name = loc.get("name", f"Station {loc_id}")
            locality = loc.get("locality") or loc.get("city") or "Coimbatore"

            country_obj = loc.get("country")
            country_name = country_obj.get("name") if isinstance(country_obj, dict) else str(country_obj or "India")

            coords = loc.get("coordinates") or {}
            loc_lat = coords.get("latitude") if isinstance(coords, dict) else None
            loc_lon = coords.get("longitude") if isinstance(coords, dict) else None

            sensors = self.fetch_location_sensors(loc_id)
            if not sensors:
                continue

            for sensor in sensors:
                sensor_id = sensor.get("id")
                sensor_name = sensor.get("name", f"Sensor {sensor_id}")

                param_obj = sensor.get("parameter") or {}
                if isinstance(param_obj, dict):
                    param_id = param_obj.get("id")
                    param_name = param_obj.get("name")
                    param_units = param_obj.get("units")
                    param_display_name = param_obj.get("displayName")
                else:
                    param_id = None
                    param_name = str(param_obj)
                    param_units = sensor.get("unit") or "µg/m³"
                    param_display_name = param_name.upper()

                raw_sensors_metadata.append({
                    "location_id": loc_id,
                    "sensor_id": sensor_id,
                    "sensor_name": sensor_name,
                    "parameter_id": param_id,
                    "parameter_name": param_name,
                    "parameter_units": param_units,
                    "parameter_display_name": param_display_name,
                })

                measurements = self.fetch_sensor_measurements(sensor_id)
                if not measurements:
                    continue

                for m in measurements:
                    val = m.get("value")
                    p_info = m.get("parameter") or {}
                    p_code = p_info.get("name") if isinstance(p_info, dict) else param_name
                    p_disp = p_info.get("displayName") if isinstance(p_info, dict) else param_display_name
                    unit_code = p_info.get("units") if isinstance(p_info, dict) else param_units

                    period = m.get("period") or {}
                    dt_from = period.get("datetimeFrom") or {}
                    dt_to = period.get("datetimeTo") or {}

                    dt_utc = dt_to.get("utc") or dt_from.get("utc") or m.get("datetime")
                    dt_local = dt_to.get("local") or dt_from.get("local")

                    m_coords = m.get("coordinates") or coords or {}
                    lat = m_coords.get("latitude") if isinstance(m_coords, dict) else loc_lat
                    lon = m_coords.get("longitude") if isinstance(m_coords, dict) else loc_lon

                    normalized_records.append({
                        "location_id": loc_id,
                        "location_name": loc_name,
                        "city": locality,
                        "country": country_name,
                        "sensor_id": sensor_id,
                        "sensor_name": sensor_name,
                        "parameter_id": param_id,
                        "parameter": p_code,
                        "parameter_display_name": p_disp,
                        "value": val,
                        "unit": unit_code,
                        "datetime_utc": dt_utc,
                        "datetime_local": dt_local,
                        "latitude": lat,
                        "longitude": lon,
                    })

        return raw_sensors_metadata, normalized_records

    def extract_location_data(
        self,
        city: str = "Coimbatore",
        coordinates: Optional[tuple] = (11.0168, 76.9558),
        limit_locations: int = 15,
    ) -> Dict[str, Any]:
        """Extract real OpenAQ location metadata and measurement observations."""
        logger.info(f"Beginning OpenAQ extraction for city: '{city}', coordinates: {coordinates}")

        raw_locations = []

        # 1. Primary location search by city
        loc_res = self.fetch_locations(city=city, limit=limit_locations)
        locations = loc_res.get("results", [])
        if locations:
            raw_locations.extend(locations)

        raw_sensors_metadata, normalized_records = self._extract_from_locations_list(locations)

        # 2. National / Active location search if 0 measurements retrieved from city
        if not normalized_records:
            logger.info("City query returned 0 measurements. Querying active national locations (country_code='IN')...")
            loc_res = self.fetch_locations(country_code="IN", limit=limit_locations)
            in_locations = loc_res.get("results", [])
            if in_locations:
                raw_locations.extend(in_locations)
                in_sensors, in_records = self._extract_from_locations_list(in_locations)
                raw_sensors_metadata.extend(in_sensors)
                normalized_records.extend(in_records)

        raw_extraction = {
            "metadata": {
                "extracted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "city": city,
                "coordinates": coordinates,
                "api_version": "v3",
                "total_locations": len(raw_locations),
                "total_sensors": len(raw_sensors_metadata),
                "total_measurements": len(normalized_records),
                "is_real_data": True,
            },
            "locations": raw_locations,
            "sensors": raw_sensors_metadata,
            "measurements": normalized_records,
        }

        logger.info(
            f"OpenAQ Extraction Summary: Locations={len(raw_locations)}, "
            f"Sensors={len(raw_sensors_metadata)}, Real Measurements={len(normalized_records)}"
        )
        return raw_extraction

    def save_raw_json(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save real raw OpenAQ JSON under data/raw/openaq/."""
        if not filename:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"openaq_raw_{timestamp}.json"

        file_path = RAW_OPENAQ_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved real raw OpenAQ response to: {file_path}")
        return str(file_path)


def run_openaq_extraction(city: str = "Coimbatore") -> str:
    """Entry point function to execute real OpenAQ extraction."""
    extractor = OpenAQExtractor()
    raw_data = extractor.extract_location_data(city=city)
    filepath = extractor.save_raw_json(raw_data)
    return filepath


if __name__ == "__main__":
    run_openaq_extraction()
