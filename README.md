# Environmental Intelligence Pipeline: EDA & ETL Foundation

A data engineering foundation for **OpenAQ Air Quality Data** and **USGS Earthquake Hazards Data**. The project implements modular extraction, schema transformation, idempotent relational database loading (PostgreSQL / SQLite), exploratory data analysis (EDA) notebooks, comprehensive unit testing, and API response specifications for future FastAPI and React dashboard integration.

---

## 1. Project Structure

```text
Environmental-Intelligence-Pipeline/
│
├── data/
│   ├── raw/
│   │   ├── openaq/          # Raw JSON responses from OpenAQ v3 API
│   │   └── usgs/            # Raw GeoJSON responses from USGS Earthquake API
│   │
│   └── processed/
│       ├── openaq/          # Analysis-ready OpenAQ CSV & Parquet files
│       └── usgs/            # Analysis-ready USGS CSV & Parquet files
│
├── etl/
│   ├── extraction/
│   │   ├── openaq_extract.py # OpenAQ v3 API data extractor
│   │   └── usgs_extract.py   # USGS Earthquake GeoJSON API extractor
│   │
│   ├── transformation/
│   │   ├── openaq_transform.py # OpenAQ cleaner, unit normalizer & US EPA AQI calculator
│   │   └── usgs_transform.py   # USGS deduplicator, datetime converter & magnitude bucketer
│   │
│   └── loading/
│       └── load.py           # Idempotent database schema loader with upsert logic
│
├── notebooks/
│   ├── air_quality_eda.ipynb  # Comprehensive OpenAQ exploratory analysis notebook
│   └── earthquake_eda.ipynb   # Comprehensive USGS earthquake exploratory analysis notebook
│
├── database/
│   └── schema.sql            # PostgreSQL relational DDL schema (locations, readings, events, pipeline_runs)
│
├── config/
│   └── config.py             # Central configuration loader using python-dotenv
│
├── tests/
│   ├── test_openaq_extract.py # Unit tests for OpenAQ extraction logic
│   ├── test_usgs_extract.py   # Unit tests for USGS extraction logic
│   ├── test_transformations.py# Unit tests for cleaning & transformation logic
│   └── test_loading.py        # Unit tests for database loading & upsert idempotency
│
├── EDA_FINDINGS.md           # Summary report of data quality, findings, and dashboard API specs
├── .env                       # Local environment variables (git-ignored)
├── .env.example               # Template environment configuration file
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python project dependencies
└── README.md                  # Project documentation
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
- `POSTGRES_DB`: Target database name (`environmental_db`).
- `POSTGRES_USER`: Database username (`postgres`).
- `POSTGRES_PASSWORD`: Database password.

> [!NOTE]
> OpenAQ v3 API mandates an API key supplied via the `X-API-Key` HTTP header (`v2` is deprecated HTTP 410). If `OPENAQ_API_KEY` is not configured, the extractor outputs a clear log notification and gracefully provides realistic sample structures for offline development.

---

## 3. Pipeline Execution Workflow

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
*Initializes relational schema from `database/schema.sql` and performs idempotent upsert loading (`ON CONFLICT DO UPDATE`) into PostgreSQL or SQLite fallback.*

---

## 4. Exploratory Data Analysis Notebooks

Launch Jupyter Notebook to view and run the interactive EDA notebooks:

```powershell
jupyter notebook
```

- **Air Quality EDA**: `notebooks/air_quality_eda.ipynb`
- **Earthquake EDA**: `notebooks/earthquake_eda.ipynb`

To programmatically execute notebooks:
```powershell
jupyter nbconvert --to notebook --execute notebooks/air_quality_eda.ipynb --output air_quality_eda.ipynb
jupyter nbconvert --to notebook --execute notebooks/earthquake_eda.ipynb --output earthquake_eda.ipynb
```

---

## 5. Automated Unit Tests

Run the complete test suite using `unittest`:

```powershell
python -m unittest discover -s tests
```

Tests verify API extraction formats, parameter parsing, unit conversions, EPA AQI calculation, magnitude bucketing, and database upsert idempotency.

---

## 6. Summary Findings & Future Dashboard Specifications

Detailed findings on air quality patterns, earthquake magnitude distributions, data quality, database aggregations, and FastAPI / React dashboard API specifications are documented in:

📄 [EDA_FINDINGS.md](file:///e:/Ranjith/Semester%209/Data%20Engineering/Project/EDA_FINDINGS.md)
