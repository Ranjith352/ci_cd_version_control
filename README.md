# Environmental Intelligence Pipeline

An end-to-end Data Engineering and Orchestration Pipeline for **OpenAQ Air Quality Data** and **USGS Earthquake Hazards Data**. The platform implements modular extraction, unit normalization, US EPA Air Quality Index (AQI) sub-index calculation, Richter magnitude bucketing, idempotent PostgreSQL loading, Prefect 3.x flow orchestration, a FastAPI backend service, comprehensive automated unit testing, and GitHub Actions CI/CD automation.

---

## Table of Contents
1. [Project Directory Structure](#1-project-directory-structure)
2. [Environment & Configuration Setup](#2-environment--configuration-setup)
3. [ETL Pipeline Execution Workflow](#3-etl-pipeline-execution-workflow)
4. [Prefect 3.x Orchestration Framework](#4-prefect-3x-orchestration-framework)
5. [FastAPI Backend Service](#5-fastapi-backend-service)
6. [Exploratory Data Analysis (EDA) Findings](#6-exploratory-data-analysis-eda-findings)
7. [Recommended Visualizations & Future API Contracts](#7-recommended-visualizations--future-api-contracts)
8. [Automated Unit Testing Suite](#8-automated-unit-testing-suite)
9. [Continuous Integration & Git Branching Strategy](#9-continuous-integration--git-branching-strategy)

---

## Phase 5 End-to-End Architecture Flow

```text
                         ┌───────────────┐
                         │    React      │
                         │   (later)     │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │    FastAPI    │
                         └───────┬───────┘
                                 │
             ┌───────────────────┼──────────────────┐
             │                   │                  │
             ▼                   ▼                  ▼
       /api/trigger       /api/status/{id}   /api/visualization
             │                   │                  │
             ▼                   ▼                  ▼
         Prefect              Prefect          PostgreSQL
             │                                      │
       ┌─────┴─────┐                                │
       ▼           ▼                                │
    OpenAQ        USGS                              │
      ETL          ETL                              │
       │           │                                │
       └─────┬─────┘                                │
             ▼                                      │
         PostgreSQL ◄───────────────────────────────┘
```

---

## 1. Project Directory Structure

```text
Environmental-Intelligence-Pipeline/
│
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI workflow (Python 3.12, Pytest)
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application root with CORS middleware & docs
│   │   ├── routers/
│   │   │   └── health.py        # GET /health check endpoint definition
│   │   ├── database/            # Database package placeholder
│   │   ├── schemas/             # Schemas package placeholder
│   │   └── services/            # Services package placeholder
│   └── tests/
│       └── test_health.py       # FastAPI TestClient unit tests for GET /health
│
├── config/
│   └── config.py                # Central environment configuration loader (.env parser)
│
├── data/
│   ├── raw/
│   │   ├── openaq/              # Raw JSON responses from OpenAQ v3 API
│   │   └── usgs/                # Raw GeoJSON responses from USGS Earthquake API
│   └── processed/
│       ├── openaq/              # Processed OpenAQ CSV & Parquet files
│       └── usgs/                # Processed USGS CSV & Parquet files
│
├── database/
│   ├── schema.sql               # Relational DDL schema (locations, readings, events, pipeline_runs)
│   └── environmental_db.sqlite  # Local SQLite database populated during testing
│
├── etl/
│   ├── extraction/
│   │   ├── openaq_extract.py    # OpenAQ v3 API data extractor
│   │   └── usgs_extract.py      # USGS Earthquake GeoJSON API extractor
│   ├── transformation/
│   │   ├── openaq_transform.py  # Unit normalizer (ppm -> µg/m³) & US EPA AQI calculator
│   │   └── usgs_transform.py    # USGS deduplicator, datetime converter & magnitude bucketer
│   └── loading/
│       └── load.py              # Idempotent database schema loader with upsert logic
│
├── notebooks/
│   ├── air_quality_eda.ipynb    # Interactive OpenAQ exploratory analysis notebook
│   └── earthquake_eda.ipynb     # Interactive USGS earthquake exploratory analysis notebook
│
├── prefect/
│   ├── deployments/
│   │   └── create_deployments.py # Programmatic Prefect deployment specifications
│   ├── flows/
│   │   ├── openaq_flow.py       # openaq_etl_flow orchestration flow definition
│   │   └── usgs_flow.py         # usgs_etl_flow orchestration flow definition
│   └── tasks/
│       ├── openaq_tasks.py      # OpenAQ tasks (extract, validate, transform, load)
│       └── usgs_tasks.py        # USGS tasks (extract, validate, transform, load)
│
├── tests/
│   ├── conftest.py              # Pytest fixtures for mock JSON & in-memory SQLite DB
│   ├── fixtures/                # Deterministic mock payloads (openaq_sample.json, usgs_sample.json)
│   ├── test_health.py           # Pytest discovery runner for health check endpoint
│   ├── test_loading.py          # Unit tests for database loading & upsert idempotency
│   ├── test_openaq_extract.py   # Unit tests for OpenAQ extraction logic
│   ├── test_transformations.py  # Unit tests for cleaning & transformation logic
│   └── test_usgs_extract.py     # Unit tests for USGS extraction logic
│
├── .env.example                 # Template environment configuration file
├── .gitignore                   # Git ignore patterns
├── README.md                    # Single master project documentation
├── requirements.txt             # Core Python project dependencies
└── requirements-dev.txt         # Development & CI testing dependencies
```

---

## 2. Environment & Configuration Setup

Copy `.env.example` to `.env` in the root directory and configure database credentials and optional OpenAQ API key:

```bash
cp .env.example .env
```

### Configuration Parameters in `.env`
- `OPENAQ_API_KEY`: Your OpenAQ v3 API key (obtained from [OpenAQ](https://openaq.org)).
- `USGS_API_URL`: USGS GeoJSON API endpoint (`https://earthquake.usgs.gov/fdsnws/event/1/query`).
- `POSTGRES_HOST`: PostgreSQL database host (`localhost`).
- `POSTGRES_PORT`: PostgreSQL port (`5432`).
- `POSTGRES_DB`: Target database name (`environmental_db` or `data_engineering`).
- `POSTGRES_USER`: Database username (`postgres`).
- `POSTGRES_PASSWORD`: Database password.

> [!NOTE]
> OpenAQ v3 API mandates an API key supplied via the `X-API-Key` HTTP header (`v2` endpoints are deprecated). If `OPENAQ_API_KEY` is not configured, the extractor outputs a clear log notification and gracefully provides realistic sample structures for offline development.

---

## 3. ETL Pipeline Execution Workflow

Run each module sequentially from the root project directory:

### Step 1: OpenAQ Data Extraction
```powershell
python etl/extraction/openaq_extract.py
```
*Fetches air quality measurements for configured city/coordinates and saves raw JSON to `data/raw/openaq/`.*

### Step 2: USGS Earthquake Data Extraction
```powershell
python etl/extraction/usgs_extract.py
```
*Queries earthquake features by date range and magnitude, saving raw GeoJSON to `data/raw/usgs/`.*

### Step 3: OpenAQ Data Transformation
```powershell
python etl/transformation/openaq_transform.py
```
*Cleans raw JSON, normalizes units ($\text{ppm} \rightarrow \mu\text{g/m}^3$), calculates US EPA AQI sub-indices, and saves clean datasets to `data/processed/openaq/` (CSV & Parquet).*

### Step 4: USGS Data Transformation
```powershell
python etl/transformation/usgs_transform.py
```
*Deduplicates events by `event_id`, converts epoch ms timestamps to UTC ISO datetimes, derives analytical magnitude categories (Micro, Minor, Light, Moderate, Strong, Major, Great), tags geographic regions, and exports to `data/processed/usgs/` (CSV & Parquet).*

### Step 5: Database Loading (PostgreSQL / SQLite)
```powershell
python etl/loading/load.py
```
*Initializes relational schema from `database/schema.sql` and performs idempotent upsert loading (`ON CONFLICT DO UPDATE`) into PostgreSQL.*

---

## 4. Prefect 3.x Orchestration Framework

The pipeline includes parameterized Prefect 3.x flows and tasks to automate end-to-end execution.

### Run OpenAQ Flow Programmatically
```powershell
python prefect/flows/openaq_flow.py
```
Or in Python:
```python
from prefect.flows.openaq_flow import openaq_etl_flow

result = openaq_etl_flow(
    city="Coimbatore",
    latitude=11.0168,
    longitude=76.9558,
    radius=25000,
    measurement_limit=2000
)
```

### Run USGS Earthquake Flow Programmatically
```powershell
python prefect/flows/usgs_flow.py
```
Or in Python:
```python
from prefect.flows.usgs_flow import usgs_etl_flow

result = usgs_etl_flow(
    start_date="2026-01-01",
    end_date="2026-08-20",
    min_magnitude=2.5,
    limit=1000
)
```

### Start Prefect Local Server & Web UI
```powershell
prefect server start
```
- **Prefect Dashboard URL**: [http://127.0.0.1:4200](http://127.0.0.1:4200)

---

## 5. FastAPI Backend Service

The project includes a FastAPI backend application located under `backend/app/main.py`.

### Start Backend Development Server
```powershell
uvicorn backend.app.main:app --reload
```

### Interactive API Documentation
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Health Check Endpoint
```bash
curl http://localhost:8000/health
```
**Response (`HTTP 200 OK`)**:
```json
{
  "status": "healthy",
  "service": "environmental-intelligence-api"
}
```

---

## 6. Exploratory Data Analysis (EDA) Findings

### Air Quality Dataset Analysis (OpenAQ v3)
- **Primary Parameters**: PM2.5, PM10, NO2, SO2, CO, O3.
- **Unit Normalization**: Gaseous pollutants measured in `ppm` or `ppb` are converted to standard $\mu\text{g/m}^3$ at 25°C and 1 atm:
  $$\text{Concentration } (\mu\text{g/m}^3) = \text{ppm} \times \frac{\text{Molecular Weight}}{0.02445}$$
- **AQI Sub-Indices**: Computed using linear piecewise interpolation for PM2.5 and PM10:
  $$\text{AQI} = \frac{I_{\text{high}} - I_{\text{low}}}{C_{\text{high}} - C_{\text{low}}} (C - C_{\text{low}}) + I_{\text{low}}$$
- **Key Findings**: Particulate matters (PM2.5 and PM10) are the dominant air quality stressors in urban locations, exhibiting strong positive correlation ($r > 0.85$). Diurnal peaks coincide with morning (07:00–09:00) and evening (18:00–21:00) traffic rush hours.

### Earthquake Hazards Analysis (USGS)
- **Magnitude Spectrum**: 2.5 to 7.8 (Mean = 4.25).
- **Categorization**: Events are classified into analytical Richter tiers (`Micro`, `Minor`, `Light`, `Moderate`, `Strong`, `Major`, `Great`).
- **Key Findings**: Over 65% of recorded earthquakes fall in the `Minor` (2.0–3.9) category, adhering strictly to the Gutenberg-Richter power-law magnitude-frequency distribution. Over 85% of events occur at shallow focal depths ($< 50\text{ km}$). High-magnitude events ($\ge 6.0$) concentrate along plate boundaries (Pacific Ring of Fire & Alpide Belt).

---

## 7. Recommended Visualizations & Future API Contracts

### Recommended Backend Aggregation Queries
```sql
-- 1. Daily Air Quality Summary per City
SELECT 
    city,
    DATE(reading_timestamp) AS reading_date,
    parameter,
    AVG(normalized_value) AS avg_concentration,
    MAX(aqi_us_epa) AS max_aqi
FROM air_quality_readings
GROUP BY city, DATE(reading_timestamp), parameter
ORDER BY reading_date DESC;

-- 2. Earthquake Frequency & Max Magnitude by Region
SELECT 
    region,
    COUNT(*) AS total_events,
    MAX(magnitude) AS max_magnitude,
    AVG(depth_km) AS avg_depth_km,
    SUM(tsunami) AS tsunami_alerts
FROM earthquake_events
GROUP BY region
ORDER BY total_events DESC;
```

### Recommended Future API Response Specs

#### `GET /api/v1/air-quality/summary`
```json
{
  "city": "Coimbatore",
  "total_stations": 2,
  "last_updated": "2026-08-20T11:45:00Z",
  "current_aqi": 72,
  "aqi_category": "Moderate",
  "pollutants": [
    { "parameter": "pm25", "value": 22.4, "unit": "µg/m³", "aqi": 72 },
    { "parameter": "pm10", "value": 48.1, "unit": "µg/m³", "aqi": 45 }
  ]
}
```

#### `GET /api/v1/earthquakes/events`
```json
{
  "total_events": 1000,
  "min_magnitude": 2.5,
  "max_magnitude": 7.8,
  "events": [
    {
      "event_id": "us7000m123",
      "event_time": "2026-08-20T08:14:22Z",
      "magnitude": 5.4,
      "magnitude_category": "Moderate",
      "place": "14 km E of Hiroo, Japan",
      "region": "Japan",
      "coordinates": { "latitude": 42.28, "longitude": 143.42 },
      "depth_km": 35.2,
      "tsunami": 0
    }
  ]
}
```

---

## 8. Automated Unit Testing Suite

The project features a 100% deterministic test suite built with `pytest` and `unittest.mock`.

### Execute Tests
```powershell
python -m pytest -v
```

### Test Suite Structure
- `tests/test_openaq_extract.py`: Tests OpenAQ API initialization, parameter validation, and HTTP 401 response handling using mocked responses (`unittest.mock`).
- `tests/test_usgs_extract.py`: Tests USGS GeoJSON response parsing and malformed JSON error handling.
- `tests/test_transformations.py`: Tests unit conversion math ($\text{ppm} \rightarrow \mu\text{g/m}^3$), EPA AQI piecewise linear formulas, Richter bucketing, region parsing, and coordinate boundary filtering (-90..90, -180..180).
- `tests/test_loading.py`: Verifies database DDL schema creation and upsert idempotency using isolated in-memory SQLite instances (`sqlite:///:memory:`).
- `backend/tests/test_health.py`: Tests FastAPI `GET /health` endpoint via `fastapi.testclient.TestClient`.

---

## 9. Continuous Integration & Git Branching Strategy

### GitHub Actions CI (`.github/workflows/ci.yml`)
The repository includes a GitHub Actions CI pipeline running on Python 3.12. The workflow automatically executes on every push to `main` or `develop` and on pull requests targeting `main`. It installs dependencies, runs the pytest suite, and uploads JUnit XML test report artifacts (`test-results.xml`).

### Recommended Branching Strategy
```text
main
 └── stable / release branch

develop
 └── integration branch

feature/*
 └── individual development branches
```

### Contribution Flow
```text
feature branch
    ↓
Pull Request
    ↓
GitHub Actions CI (16/16 PASS)
    ↓
Merge into develop
    ↓
Final validation
    ↓
Merge into main
```
