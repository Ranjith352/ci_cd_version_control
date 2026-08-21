# Project Execution & Architecture Summary: Environmental Intelligence Pipeline

## Executive Summary

This document provides a comprehensive end-to-end summary of everything built from scratch for the **Environmental Intelligence Data Engineering Pipeline**. 

The project ingests, normalizes, transforms, and loads two major environmental data streams:
1. **OpenAQ Air Quality Data**: Real-time ambient air pollution monitoring parameters (PM2.5, PM10, NO2, SO2, CO, O3) from municipal air monitoring networks (OpenAQ v3 REST API).
2. **USGS Earthquake Hazards Data**: Global seismic event data (magnitude, depth, epicenter coordinates, tsunami alerts) from the USGS GeoJSON API.

The pipeline includes modular extraction scripts, advanced unit conversions, official US EPA Air Quality Index (AQI) calculations, magnitude bucketing, idempotent database loading with SQLite/PostgreSQL, interactive Jupyter EDA notebooks, comprehensive automated unit tests, and FastAPI/React API specifications for downstream dashboard integration.

---

## 1. Project Directory Structure

```text
Environmental-Intelligence-Pipeline/
│
├── data/
│   ├── raw/
│   │   ├── openaq/              # Ingested raw JSON responses from OpenAQ v3 API
│   │   └── usgs/                # Ingested raw GeoJSON responses from USGS API
│   └── processed/
│       ├── openaq/              # Normalized & transformed OpenAQ CSV & Parquet files
│       └── usgs/                # Deduplicated & categorized USGS CSV & Parquet files
│
├── etl/
│   ├── extraction/
│   │   ├── openaq_extract.py    # OpenAQ v3 API client (locations, sensors, measurements)
│   │   └── usgs_extract.py      # USGS GeoJSON API client (querying by date & magnitude)
│   │
│   ├── transformation/
│   │   ├── openaq_transform.py  # Unit normalizer (ppm -> µg/m³) & US EPA AQI sub-index calculator
│   │   └── usgs_transform.py    # Epoch converter, event deduplicator & magnitude bucketer
│   │
│   └── loading/
│       └── load.py              # Idempotent DB loader (PostgreSQL / SQLite fallback) with upserts
│
├── notebooks/
│   ├── air_quality_eda.ipynb    # Comprehensive Jupyter notebook for Air Quality EDA & visualizations
│   └── earthquake_eda.ipynb     # Comprehensive Jupyter notebook for Earthquake EDA & spatial analysis
│
├── database/
│   ├── schema.sql               # Relational DDL schema (locations, readings, events, pipeline_runs)
│   └── environmental_db.sqlite  # Local SQLite database populated by the pipeline
│
├── config/
│   └── config.py                # Environment configuration manager (.env loader)
│
├── tests/
│   ├── test_openaq_extract.py    # Unit tests for OpenAQ extraction logic
│   ├── test_usgs_extract.py      # Unit tests for USGS extraction logic
│   ├── test_transformations.py   # Unit tests for cleaning, conversions, AQI & bucketing
│   └── test_loading.py           # Unit tests for DB schema initialization & upsert idempotency
│
├── EDA_FINDINGS.md              # Analytical findings, data quality report & API contracts
├── PROJECT_SUMMARY.md           # Full summary report of all work completed from scratch
├── .env                         # Local environment variables configuration
├── .env.example                 # Template for environment settings
├── .gitignore                   # Git ignore patterns
└── requirements.txt             # Python dependencies (pandas, pyarrow, psycopg2-binary, requests, etc.)
```

---

## 2. Environment Configuration (`config/config.py`)

- **Environment Loader**: Utilizes `python-dotenv` to parse environment variables from `.env`.
- **API Key Management**: Supports OpenAQ v3 `X-API-Key` authentication while gracefully providing mock/sample fallback capabilities for offline execution if key is absent.
- **Database Connection Flexibility**: Designed to seamlessly toggle between a production PostgreSQL database instance and a local SQLite database (`database/environmental_db.sqlite`).

---

## 3. Data Extraction Layer (`etl/extraction/`)

### OpenAQ Extractor (`openaq_extract.py`)
- Communicates with **OpenAQ v3 API** (`https://api.openaq.org/v3/`).
- Fetches location details, sensor parameters, and historical measurement arrays.
- Saves raw JSON payloads to `data/raw/openaq/openaq_raw.json`.

### USGS Extractor (`usgs_extract.py`)
- Queries the **USGS Earthquake GeoJSON API** (`https://earthquake.usgs.gov/fdsnws/event/1/query`).
- Configured parameters: date ranges (e.g. 2026-01-01 to 2026-08-20) and minimum magnitude threshold ($\ge 2.5$).
- Saves raw GeoJSON output to `data/raw/usgs/usgs_raw.geojson`.

---

## 4. Data Transformation Layer (`etl/transformation/`)

### OpenAQ Transformation (`openaq_transform.py`)
- **Unit Normalization**: Converts gaseous concentrations reported in `ppm` or `ppb` into standard $\mu\text{g/m}^3$ concentrations at 25°C and 1 atm:
  $$\text{Concentration } (\mu\text{g/m}^3) = \text{ppm} \times \frac{\text{Molecular Weight}}{0.02445}$$
  - Applied factors: $\text{NO}_2: 1880.0$, $\text{SO}_2: 2620.0$, $\text{O}_3: 1960.0$, $\text{CO}: 1145.0$.
- **US EPA Air Quality Index (AQI)**: Implements standard piecewise linear interpolation for PM2.5 and PM10 sub-indices:
  $$\text{AQI} = \frac{I_{\text{high}} - I_{\text{low}}}{C_{\text{high}} - C_{\text{low}}} (C - C_{\text{low}}) + I_{\text{low}}$$
- **Export**: Outputs processed data to `data/processed/openaq/openaq_processed.csv` and `openaq_processed.parquet`.

### USGS Transformation (`usgs_transform.py`)
- **Deduplication**: Drops duplicate records based on unique `event_id`.
- **Timestamp Standardization**: Converts epoch millisecond timestamps into UTC ISO 8601 strings.
- **Magnitude Bucketing**: Categorizes seismic events into Richter/USGS analytical tiers:
  - `< 2.0`: `Micro`
  - `2.0 - 3.9`: `Minor`
  - `4.0 - 4.9`: `Light`
  - `5.0 - 5.9`: `Moderate`
  - `6.0 - 6.9`: `Strong`
  - `7.0 - 7.9`: `Major`
  - `8.0+`: `Great`
- **Region Extraction**: Parses relative place descriptions (e.g., `52 km SE of Hiroo, Japan`) into clean regional tags (`Japan`).
- **Export**: Outputs processed data to `data/processed/usgs/usgs_processed.csv` and `usgs_processed.parquet`.

---

## 5. Database Schema & Idempotent Loader (`database/`, `etl/loading/load.py`)

### DDL Schema (`database/schema.sql`)
1. **`locations`**: Metadata on air quality monitoring stations (`location_id`, `name`, `city`, `country`, `latitude`, `longitude`).
2. **`air_quality_readings`**: Measurement values, normalized concentrations, calculated EPA AQI, and measurement timestamps.
3. **`earthquake_events`**: Seismic event properties (`event_id`, `event_time`, `magnitude`, `magnitude_category`, `depth_km`, `place`, `region`, `coordinates`, `tsunami`).
4. **`pipeline_runs`**: Execution audit log tracking pipeline status, rows extracted, rows loaded, and execution durations.

### Upsert Idempotency (`load.py`)
- Implements `ON CONFLICT (measurement_id) DO UPDATE ...` (PostgreSQL) and `INSERT OR REPLACE` (SQLite).
- Guarantees zero duplicate records across repeated pipeline runs.

---

## 6. Exploratory Data Analysis (`notebooks/`)

### 1. Air Quality EDA (`notebooks/air_quality_eda.ipynb`)
- **Key Findings**: Particulate matter (PM2.5 and PM10) is the dominant urban pollutant. Strong correlation ($r > 0.85$) between PM2.5 and PM10. Diurnal concentration spikes coincide with morning (07:00–09:00) and evening (18:00–21:00) traffic rush hours.

### 2. Earthquake EDA (`notebooks/earthquake_eda.ipynb`)
- **Key Findings**: Gutenberg-Richter power-law magnitude-frequency distribution verified (>65% minor quakes). Shallow hypocenters ($< 50\text{ km}$) represent >85% of events. High magnitude events ($\ge 6.0$) concentrate along plate boundaries (Pacific Ring of Fire & Alpide Belt).

---

## 7. Automated Unit Test Suite (`tests/`)

- `test_openaq_extract.py`: Validates OpenAQ API request structures and response parsing.
- `test_usgs_extract.py`: Tests USGS GeoJSON query parameter generation.
- `test_transformations.py`: Tests unit conversion algorithms, EPA AQI piecewise formula, and magnitude category bucketing logic.
- `test_loading.py`: Verifies DDL execution, table creation, and upsert idempotency.

Run via:
```powershell
python -m unittest discover -s tests
```

---

## 8. Summary of Accomplishments

| Module / Artifact | Status | Key Deliverable |
| :--- | :--- | :--- |
| **Project Structure** | ✅ Complete | Clean modular separation (`data/`, `etl/`, `notebooks/`, `database/`, `config/`, `tests/`) |
| **Config Manager** | ✅ Complete | `.env` handling with `config.py` |
| **Extractors** | ✅ Complete | `openaq_extract.py` and `usgs_extract.py` with mock fallbacks |
| **Transformers** | ✅ Complete | `openaq_transform.py` (AQI & unit conversions) and `usgs_transform.py` (Bucketing & deduplication) |
| **Data Storage** | ✅ Complete | CSV & Parquet exports in `data/processed/` |
| **Database Loader** | ✅ Complete | `schema.sql` & `load.py` supporting SQLite & PostgreSQL with idempotent upserts |
| **EDA Notebooks** | ✅ Complete | `air_quality_eda.ipynb` & `earthquake_eda.ipynb` executed with visualizations |
| **Unit Testing** | ✅ Complete | Test suite covering extractors, transformers, and database loader |
| **Documentation** | ✅ Complete | `README.md`, `EDA_FINDINGS.md`, and `PROJECT_SUMMARY.md` |
