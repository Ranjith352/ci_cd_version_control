# Environmental Intelligence Pipeline

An end-to-end Data Engineering, Real-Time Streaming, and Orchestration Platform for **OpenAQ Air Quality Data** and **USGS Earthquake Hazards Data**. The platform features modular data extraction, EPA AQI calculation, Richter magnitude bucketing, idempotent PostgreSQL schema loading, Prefect 3.x orchestration, FastAPI backend services, Kafka real-time event streaming, Redis real-time state storage, WebSocket live updates, React dashboards, and complete Docker Compose containerization.

---

## PROJECT PHASE STATUS

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 1** | Data Extraction (OpenAQ v3 API & USGS GeoJSON API) | ✅ Completed |
| **Phase 2** | ETL & PostgreSQL Database Schema Loading | ✅ Completed |
| **Phase 3** | Exploratory Data Analysis (EDA) | ✅ Completed |
| **Phase 4** | Prefect 3.x Orchestration Framework | ✅ Completed |
| **Phase 5** | FastAPI Backend Service & Analytics APIs | ✅ Completed |
| **Phase 6** | React Batch Dashboard | ✅ Completed |
| **Phase 7** | Kafka Real-Time Pipeline & Redis Store | ✅ Completed |
| **Phase 8** | Dockerization & Containerized Execution | ✅ Completed |
| **Phase 9** | CI/CD Automation & Release Pipeline | ⏳ Not started / next phase |

---

## Table of Contents
1. [System Architecture](#1-system-architecture)
2. [Project Directory Structure](#2-project-directory-structure)
3. [Database Schema (PostgreSQL)](#3-database-schema-postgresql)
4. [FastAPI Backend & WebSockets](#4-fastapi-backend--websockets)
5. [Prefect 3.x Orchestration](#5-prefect-3x-orchestration)
6. [Kafka Real-Time Streaming Layer](#6-kafka-real-time-streaming-layer)
7. [React Batch & Live Dashboards](#7-react-batch--live-dashboards)
8. [Docker Infrastructure (Phase 8)](#8-docker-infrastructure-phase-8)
9. [Verification & Automated Test Suite](#9-verification--automated-test-suite)
10. [Exploratory Data Analysis (EDA) Findings](#10-exploratory-data-analysis-eda-findings)

---

## 1. System Architecture

### Batch Architecture Flow
```text
                         ┌───────────────┐
                         │ React Frontend│
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │    FastAPI    │
                         └───────┬───────┘
                                 │
                         ┌───────┴───────┐
                         ▼               ▼
                     Prefect          PostgreSQL
                         │
                   ┌─────┴─────┐
                   ▼           ▼
                OpenAQ        USGS
                  ETL          ETL
```

### Real-Time Streaming Architecture Flow
```text
OpenAQ v3 API / USGS API
           │
           ▼
     Kafka Producer
           │
           ▼
    Kafka Topics
 (air-quality-live, earthquakes-live, DLQs)
           │
           ▼
     Kafka Consumer
           │
           ▼
      Redis Store
           │
           ▼
  FastAPI WebSocket (/api/live/ws)
           │
           ▼
  React Live Dashboard
```

---

## 2. Project Directory Structure

```text
Environmental-Intelligence-Pipeline/
│
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI workflow (Python 3.12 & Pytest)
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application root & middleware setup
│   │   ├── config.py            # Backend settings and CORS origins
│   │   ├── routers/
│   │   │   ├── health.py        # GET /health health check endpoint
│   │   │   ├── trigger.py       # POST /api/trigger Prefect workflow trigger
│   │   │   ├── status.py        # GET /api/status/{run_id} run status tracker
│   │   │   ├── visualization.py # GET /api/visualization/* analytics endpoints
│   │   │   └── live.py          # GET & WS /api/live/* real-time streaming & WebSockets
│   │   ├── database/            # SQLAlchemy database connection session generator
│   │   ├── schemas/             # Pydantic API response & request schemas
│   │   └── services/            # Backend business logic services
│   └── tests/                   # Backend unit tests suite
│
├── config/
│   └── config.py                # Central environment configuration loader (.env parser)
│
├── data/
│   ├── raw/                     # Raw JSON & GeoJSON API responses
│   └── processed/               # Cleaned CSV & Parquet files
│
├── database/
│   ├── schema.sql               # PostgreSQL DDL schema definition
│   └── environmental_db.sqlite  # Local SQLite database for lightweight testing
│
├── docker/
│   ├── backend/                 # Backend Dockerfile
│   ├── consumer/                # Kafka consumer Dockerfile
│   ├── frontend/                # Frontend Dockerfile (Nginx multi-stage)
│   └── producer/                # Kafka producer Dockerfile
│
├── etl/
│   ├── extraction/              # OpenAQ & USGS extractors
│   ├── transformation/          # Normalization, EPA AQI & Richter categorizer
│   └── loading/                 # Idempotent PostgreSQL loading logic
│
├── frontend/
│   ├── src/                     # React 18 component source tree
│   │   ├── components/          # Reusable UI components & Recharts visualizers
│   │   ├── pages/               # Batch Dashboard & Live Monitoring pages
│   │   ├── services/            # Axios API client & WebSocket connector
│   │   └── test/                # Vitest & React Testing Library test suite
│   ├── package.json             # Frontend dependencies & scripts
│   └── vite.config.js           # Vite build configuration
│
├── kafka/
│   ├── consumer/                # Real-time Kafka consumer workers
│   ├── producer/                # Real-time Kafka producer polling services
│   ├── schemas/                 # Pydantic event schemas
│   ├── utils/                   # Redis client & Kafka health utilities
│   └── setup_topics.py          # Automated topic creation script
│
├── notebooks/
│   ├── air_quality_eda.ipynb    # Interactive OpenAQ EDA notebook
│   └── earthquake_eda.ipynb     # Interactive USGS earthquake EDA notebook
│
├── prefect/
│   ├── flows/                   # openaq_etl_flow & usgs_etl_flow definitions
│   └── tasks/                   # Modular Prefect tasks
│
├── tests/                       # Comprehensive Python unit test suite
├── .env.example                 # Template environment configuration file
├── .gitignore                   # Version control ignore patterns
├── docker-compose.yml           # Complete containerized multi-service orchestration
├── EDA_FINDINGS.md              # Exploratory Data Analysis summary document
├── README.md                    # Single master project documentation
├── requirements.txt             # Core Python production dependencies
└── requirements-dev.txt         # Development & testing dependencies
```

---

## 3. Database Schema (PostgreSQL)

- **Database Engine**: PostgreSQL 15
- **Production Database Name**: `data_engineering`
- **Schema Definition**: [`database/schema.sql`](database/schema.sql)

### Tables Summary

1. `locations`
   - Primary key: `location_id`
   - Attributes: `location_name`, `city`, `country`, `latitude`, `longitude`, `updated_at`

2. `air_quality_readings`
   - Primary key: `measurement_id`
   - Foreign key: `location_id` $\rightarrow$ `locations(location_id)`
   - Attributes: `parameter`, `value`, `unit`, `normalized_value`, `normalized_unit`, `aqi_us_epa`, `reading_timestamp`, `created_at`
   - Constraint: `UNIQUE(location_id, parameter, reading_timestamp)` for idempotent loading

3. `earthquake_events`
   - Primary key: `event_id`
   - Attributes: `event_time`, `magnitude`, `magnitude_type`, `place`, `region`, `longitude`, `latitude`, `depth_km`, `magnitude_category`, `status`, `event_type`, `tsunami`, `event_url`, `created_at`

4. `pipeline_runs`
   - Primary key: `run_id`
   - Attributes: `pipeline_name`, `records_extracted`, `records_loaded`, `status`, `started_at`, `completed_at`, `error_message`

---

## 4. FastAPI Backend & WebSockets

### Verified API Endpoints

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/health` | `GET` | Application health check endpoint |
| `/api/trigger` | `POST` | Trigger background Prefect flow execution (`openaq` or `usgs`) |
| `/api/status/{run_id}` | `GET` | Fetch Prefect flow execution status and record metrics |
| `/api/visualization/air-quality` | `GET` | Query daily air quality concentration averages & EPA AQI scores |
| `/api/visualization/earthquakes` | `GET` | Query earthquake events and regional aggregated summaries |
| `/api/analytics/trends` | `GET` | Query independent daily PM2.5 averages & earthquake event counts |
| `/api/live/air-quality` | `GET` | Query recent real-time OpenAQ measurements from Redis store |
| `/api/live/earthquakes` | `GET` | Query recent real-time USGS earthquake events from Redis store |
| `/api/live/health` | `GET` | Verify connectivity status for Kafka broker and Redis store |
| `/api/live/ws` | `WS` | WebSocket endpoint streaming real-time environmental events to React |

---

## 5. Prefect 3.x Orchestration

The pipeline uses Prefect 3.x flows for workflow orchestration:

- **`openaq_etl_flow`**: Orchestrates OpenAQ v3 data extraction, parameter validation, unit normalization, EPA AQI computation, and PostgreSQL loading.
  - *Parameters*: `city`, `latitude`, `longitude`, `radius`, `measurement_limit`
- **`usgs_etl_flow`**: Orchestrates USGS GeoJSON earthquake extraction, coordinate boundary validation, Richter tier categorisation, region tagging, and PostgreSQL loading.
  - *Parameters*: `start_date`, `end_date`, `min_magnitude`, `limit`

Features include automated retries, error logging, parameter validation, and idempotent loading into PostgreSQL.

---

## 6. Kafka Real-Time Streaming Layer

The real-time streaming pipeline continuously ingests environmental events:

- **Kafka Topics**:
  - `air-quality-live`: Live OpenAQ air quality telemetry stream
  - `earthquakes-live`: Live USGS earthquake hazard stream
  - `air-quality-dlq`: Dead Letter Queue for malformed air quality payloads
  - `earthquakes-dlq`: Dead Letter Queue for malformed earthquake payloads
- **Redis Store**: In-memory caching layer maintaining recent telemetry snapshots for quick API serving.
- **WebSocket Gateway**: High-efficiency WebSocket connection handling (`/api/live/ws`) with automated client heartbeats and snapshot delivery.

---

## 7. React Batch & Live Dashboards

The React frontend (`frontend/`) provides interactive data visualization:

- **Batch Dashboard**: Trigger pipeline runs, view execution progress, inspect air quality trends, and explore regional earthquake maps.
- **Live Monitoring Dashboard**: Connects to FastAPI WebSockets for real-time telemetry updates with connection status indicators.

---

## 8. Docker Infrastructure (Phase 8)

The application stack is containerized using Docker Compose (`docker-compose.yml`):

| Service | Container Image / Dockerfile | Internal Port | Host Port |
| :--- | :--- | :--- | :--- |
| **postgres** | `postgres:15-alpine` | `5432` | `5432` |
| **redis** | `redis:7-alpine` | `6379` | `6379` |
| **kafka** | `apache/kafka:latest` | `9092` | `9092`, `9094` |
| **kafka-topic-init** | `docker/backend/Dockerfile` | N/A | N/A |
| **prefect-server** | `prefecthq/prefect:3-python3.12` | `4200` | `4200` |
| **backend** | `docker/backend/Dockerfile` | `8000` | `8000` |
| **kafka-producer** | `docker/producer/Dockerfile` | N/A | N/A |
| **kafka-consumer** | `docker/consumer/Dockerfile` | N/A | N/A |
| **frontend** | `docker/frontend/Dockerfile` | `80` | `80` |

### Verified Docker Management Commands

```powershell
# 1. Validate Docker Compose configuration file
docker compose config

# 2. Build service images
docker compose build

# 3. Start containerized stack in detached mode
docker compose up -d

# 4. Check service status
docker compose ps

# 5. View service logs
docker compose logs -f backend
```

---

## 9. Verification & Automated Test Suite

### Verification Metrics

- **Python Tests**: 42 passed (100% deterministic suite covering ETL, Prefect, FastAPI, and Kafka schema handlers)
- **Frontend Tests**: 6 passed (Vitest & React Testing Library components suite)
- **Frontend Build**: Vite production build succeeded (`dist/` bundle created)
- **Docker Stack Validation**: `docker compose config` validated successfully

### Running Tests Locally

```powershell
# Run Python backend & pipeline unit test suite
.venv\Scripts\python.exe -m pytest -v

# Run React frontend component tests
cd frontend
npm test

# Run React frontend production build
npm run build
```

---

## 10. Exploratory Data Analysis (EDA) Findings

Summary of key EDA findings (see [`EDA_FINDINGS.md`](EDA_FINDINGS.md) for detailed reports):

- **Air Quality**: Fine particulates ($\text{PM}_{2.5}$) and coarse particulates ($\text{PM}_{10}$) exhibit strong positive correlation ($r > 0.85$). Traffic rush hours ($07:00\text{--}09:00$ and $18:00\text{--}21:00$) correlate with daily peak pollutant concentrations.
- **Earthquake Hazards**: Over $65\%$ of seismic events belong to the `Minor` ($2.0\text{--}3.9$) Richter magnitude category, following Gutenberg-Richter power-law distributions. Over $85\%$ of events occur at shallow depths ($< 50\text{ km}$). High-magnitude earthquakes ($\ge 6.0$) cluster along active tectonic plate margins.
