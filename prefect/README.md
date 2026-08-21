# Prefect 3.x Orchestration Framework

This module orchestrates the **Environmental Intelligence Data Engineering Pipeline** using Prefect 3.x flows and tasks.

---

## 1. Directory Structure

```text
prefect/
├── flows/
│   ├── openaq_flow.py      # openaq_etl_flow definition & flow execution
│   └── usgs_flow.py        # usgs_etl_flow definition & flow execution
├── tasks/
│   ├── openaq_tasks.py     # OpenAQ extract, validate, transform, load tasks
│   └── usgs_tasks.py       # USGS extract, validate, transform, load tasks
├── deployments/
│   └── create_deployments.py # Programmatic Prefect deployment specifications
└── README.md
```

---

## 2. Prefect Local Server Commands

### Start Prefect Server
Launch the local Prefect orchestration server and Web UI:
```powershell
prefect server start
```
*Prefect Dashboard URL: [http://127.0.0.1:4200](http://127.0.0.1:4200)*

### Verify Prefect CLI & Work Pools
Check installed Prefect version:
```powershell
prefect version
```

List active work pools:
```powershell
prefect work-pool ls
```

---

## 3. Running Flows Programmatically

### Run OpenAQ Air Quality Flow
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
print(result)
```

### Run USGS Earthquake Flow
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
print(result)
```

---

## 4. Key Design Principles
- **No Direct Logic Modification**: Business logic in `etl/` remains clean and decoupled.
- **PostgreSQL Enforcement**: Direct PostgreSQL loading into target database `data_engineering`; silent fallback to SQLite is disabled.
- **Strict Data Validation**: Extraction and transformation outputs are validated for non-emptiness, valid schemas, coordinate boundaries (-90..90, -180..180), numeric types, and timestamp formatting before loading.
- **Idempotency**: PostgreSQL `ON CONFLICT DO UPDATE` upserts guarantee zero duplicate records across repeated flow runs.
