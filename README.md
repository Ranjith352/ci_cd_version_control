# Environmental Intelligence Pipeline: EDA & ETL Foundation

A data engineering foundation for **OpenAQ Air Quality Data** and **USGS Earthquake Hazards Data**. The project implements modular extraction, schema transformation, idempotent relational database loading (PostgreSQL / SQLite), exploratory data analysis (EDA) notebooks, comprehensive unit testing, Prefect flow orchestration, and GitHub Actions CI/CD automation.

---

## 1. Project Structure

```text
Environmental-Intelligence-Pipeline/
│
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI workflow (Python 3.12, Pytest)
│
├── data/
│   ├── raw/
│   │   ├── openaq/              # Raw JSON responses from OpenAQ v3 API
│   │   └── usgs/                # Raw GeoJSON responses from USGS Earthquake API
│   │
│   └── processed/
│       ├── openaq/              # Analysis-ready OpenAQ CSV & Parquet files
│       └── usgs/                # Analysis-ready USGS CSV & Parquet files
│
├── etl/
│   ├── extraction/
│   │   ├── openaq_extract.py    # OpenAQ v3 API data extractor
│   │   └── usgs_extract.py      # USGS Earthquake GeoJSON API extractor
│   │
│   ├── transformation/
│   │   ├── openaq_transform.py  # OpenAQ cleaner, unit normalizer & US EPA AQI calculator
│   │   └── usgs_transform.py    # USGS deduplicator, datetime converter & magnitude bucketer
│   │
│   └── loading/
│       └── load.py              # Idempotent database schema loader with upsert logic
│
├── prefect/
│   ├── flows/
│   │   ├── openaq_flow.py       # openaq_etl_flow Prefect orchestration definition
│   │   └── usgs_flow.py         # usgs_etl_flow Prefect orchestration definition
│   ├── tasks/
│   │   ├── openaq_tasks.py      # OpenAQ task definitions (extract, validate, transform, load)
│   │   └── usgs_tasks.py        # USGS task definitions (extract, validate, transform, load)
│   └── README.md                # Prefect documentation & local server guide
│
├── notebooks/
│   ├── air_quality_eda.ipynb    # Comprehensive OpenAQ exploratory analysis notebook
│   └── earthquake_eda.ipynb     # Comprehensive USGS earthquake exploratory analysis notebook
│
├── database/
│   └── schema.sql               # PostgreSQL relational DDL schema (locations, readings, events, pipeline_runs)
│
├── config/
│   └── config.py                # Central configuration loader using python-dotenv
│
├── tests/
│   ├── conftest.py              # Pytest fixtures for mock JSON & in-memory SQLite DB
│   ├── fixtures/                # Mock data fixtures (openaq_sample.json, usgs_sample.json)
│   ├── test_openaq_extract.py   # Unit tests for OpenAQ extraction logic
│   ├── test_usgs_extract.py     # Unit tests for USGS extraction logic
│   ├── test_transformations.py  # Unit tests for cleaning & transformation logic
│   └── test_loading.py          # Unit tests for database loading & upsert idempotency
│
├── EDA_FINDINGS.md              # Summary report of data quality, findings, and dashboard API specs
├── PROJECT_SUMMARY.md           # Full pipeline execution & architecture summary
├── .env                         # Local environment variables (git-ignored)
├── .env.example                 # Template environment configuration file
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Core Python project dependencies
├── requirements-dev.txt         # Development & CI test dependencies
└── README.md                    # Project documentation
```

---

## 2. API & Environment Configuration

Copy `.env.example` to `.env` and fill in your database credentials and optional OpenAQ API key:

```bash
cp .env.example .env
```

Configuration Parameters in `.env`:
- `OPENAQ_API_KEY`: Your OpenAQ v3 API key (obtained from [OpenAQ](https://openaq.org)).
- `USGS_API_URL`: USGS GeoJSON API endpoint (`https://earthquake.usgs.gov/fdsnws/event/1/query`).
- `POSTGRES_HOST`: PostgreSQL database host (`localhost`).
- `POSTGRES_PORT`: PostgreSQL port (`5432`).
- `POSTGRES_DB`: Target database name (`environmental_db` or `data_engineering`).
- `POSTGRES_USER`: Database username (`postgres`).
- `POSTGRES_PASSWORD`: Database password.

---

## 3. Pipeline Execution Workflow

Run each module sequentially from the root project directory:

### Step 1: OpenAQ Data Extraction
```powershell
python etl/extraction/openaq_extract.py
```

### Step 2: USGS Earthquake Data Extraction
```powershell
python etl/extraction/usgs_extract.py
```

### Step 3: OpenAQ Data Transformation
```powershell
python etl/transformation/openaq_transform.py
```

### Step 4: USGS Data Transformation
```powershell
python etl/transformation/usgs_transform.py
```

### Step 5: Database Loading (PostgreSQL / SQLite)
```powershell
python etl/loading/load.py
```

---

## 4. Prefect Orchestration Flows

Run the Prefect 3.x orchestration flows:
```powershell
python prefect/flows/openaq_flow.py
python prefect/flows/usgs_flow.py
```

Launch the local Prefect Web UI server:
```powershell
prefect server start
```

---

## 5. Automated Unit Tests

Run the complete deterministic test suite using `pytest`:

```powershell
python -m pytest -v
```

Tests use deterministic fixtures and mocked external APIs (`unittest.mock`), ensuring 100% offline pass capability without requiring live network access or real production database credentials.

---

## 6. Continuous Integration & Git Branching Strategy

### CI Workflow (`.github/workflows/ci.yml`)
The project utilizes GitHub Actions CI running on Python 3.12. The workflow automatically executes on every push to `main` or `develop` and on pull requests targeting `main`. It runs the 14-test deterministic suite and uploads JUnit XML test report artifacts (`test-results.xml`) for every build.

### Recommended Branching Strategy
```text
main
 └── stable / release branch

develop
 └── integration branch

feature/*
 └── individual development branches
```

### Development Flow
```text
feature branch
    ↓
Pull Request
    ↓
GitHub Actions CI (14/14 tests pass)
    ↓
Merge into develop
    ↓
Final validation
    ↓
Merge into main
```

---

## 7. Summary Findings & Future Dashboard Specifications

Detailed findings on air quality patterns, earthquake magnitude distributions, data quality, database aggregations, and FastAPI / React dashboard API specifications are documented in:

📄 [EDA_FINDINGS.md](file:///e:/Ranjith/Semester%209/Data%20Engineering/Project/EDA_FINDINGS.md)
