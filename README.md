# NASA Near-Earth Asteroid Hazard Analysis

## Project Question

**Which asteroid features are linked to a “potentially hazardous” label?**

This project uses NASA's Near Earth Object Web Service (NeoWs) to collect data about near-Earth asteroids, their orbital characteristics, and close approaches. Asteroid, orbit, and close-approach data are connected using the asteroid ID to compare potentially hazardous and non-hazardous asteroids.

The project investigates which orbital and close-approach features are associated with the potentially hazardous label. A simple classifier will be developed in a later stage. Since the hazard label is built from absolute magnitude (H) and minimum orbit intersection distance (MOID), H, MOID, and diameter will not be used as model features. The hazard label is treated as a screening label, not an impact forecast.

---

## Data Sources

### NASA Near Earth Object Web Service (NeoWs)

The primary data source is NASA's Near Earth Object Web Service (NeoWs), a public REST API that provides JSON data about near-Earth asteroids.

The project uses the following NeoWs endpoints:

- **Browse** — provides the asteroid catalogue.
- **Feed** — provides close-approach data for a specified date range.
- **Lookup** — provides detailed information about an individual asteroid.

Official NASA API documentation:

https://api.nasa.gov/#asteroids-neows

Detailed source and provenance information is available in [`docs/sources.md`](docs/sources.md).

The API requires a NASA API key. The key must be provided through an environment variable and must never be committed to the repository.

### Data Entities

The project organizes the collected data into three entities:

- **`asteroids`** — one row per asteroid.
- **`orbits`** — one row per asteroid orbit.
- **`approaches`** — one row per close-approach event.

The tables are connected using the asteroid identifier.

The initial data collection target is at least 5,000 asteroids and their associated close-approach data.

---

## How to Run

### Prerequisites

- Python 3
- Git
- A NASA API key from the [NASA API portal](https://api.nasa.gov/)

### 1. Clone the repository

```bash
git clone https://github.com/se-220717030/nasa-data-pipeline.git
cd nasa-data-pipeline
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows:**

```powershell
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the NASA API key

Create a local `.env` file in the repository root and configure the NASA API key using the environment variable expected by the ingestion script.

Check `.env.example` for the required variable name and format.

Never commit the `.env` file or expose API credentials in the repository.

### 6. Run the ingestion script

From the repository root, run:

```bash
python src/ingest.py
```

The ingestion script retrieves data from the approved NASA NeoWs endpoints and saves the raw responses in `data/raw/`.

Each run preserves the original responses and uses UTC retrieval timestamps in filenames. Subsequent runs create new files rather than overwriting previously retrieved files.

---

## Repository Structure

```text
nasa-data-pipeline/
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── data/
│   └── raw/
├── docs/
│   └── sources.md
├── sql/
│   ├── schema.sql
│   └── queries/
└── src/
    ├── ingest.py
    ├── db.py
    ├── load.py
    └── checks.py
```

The structure above includes the planned M2 files. If `load.py`, `checks.py`, or the analytical query has not yet been added to the repository, those entries should be treated as planned until the corresponding files exist.

### Directory and File Descriptions

| Path | Description |
|---|---|
| `README.md` | Project overview, data model, and instructions |
| `.gitignore` | Specifies files and directories Git should ignore |
| `.env.example` | Documents the required environment variables |
| `requirements.txt` | Lists the required Python dependencies |
| `data/raw/` | Stores raw data retrieved during ingestion |
| `data/asteroids.db` | Generated SQLite database; not committed to Git |
| `src/ingest.py` | Retrieves raw data from NASA NeoWs |
| `src/db.py` | Provides the database connection and initialization functions |
| `src/load.py` | Loads and validates raw data in the database |
| `src/checks.py` | Runs database integrity and loading checks |
| `sql/schema.sql` | Defines database tables, constraints, and indexes |
| `sql/queries/` | Stores analytical SQL queries |
| `docs/sources.md` | Documents data sources and provenance |

---

## Ingestion Scope — M1

Milestone M1 focuses on the ingestion stage of the data engineering lifecycle.

The ingestion script is designed to:

1. Retrieve data from the approved NASA NeoWs sources.
2. Save raw responses without cleaning, filtering, renaming, or reshaping them.
3. Include UTC retrieval timestamps in saved filenames.
4. Create new files on subsequent runs without overwriting previous files.
5. Read credentials from environment variables.
6. Handle request failures, timeouts, rate limits, and server errors.
7. Report the retrieved sources, record or file counts, and any errors.

Data cleaning, transformation, feature engineering, database loading, and machine learning are outside the scope of M1.

---

## Database Schema and Data Model — M2

Milestone M2 introduces a relational SQLite database to organize the collected NASA NeoWs data for further analysis.

### Database Tables

#### `asteroids`

Stores one record per asteroid. The table includes:

- `asteroid_key` — surrogate primary key.
- `source_id` — required, unique NASA source identifier.
- `name` and `designation` — asteroid identification fields.
- `absolute_magnitude_h` — absolute magnitude.
- `is_potentially_hazardous` — potentially hazardous status.
- `is_sentry_object` — Sentry object status.
- `diameter_min_km` and `diameter_max_km` — estimated diameter bounds.
- `retrieved_at` — UTC retrieval timestamp.

#### `orbits`

Stores orbital characteristics for each asteroid, including eccentricity, inclination, semi-major axis, orbital period, minimum orbit intersection distance, and orbit classification.

The table uses `orbit_key` as its surrogate primary key and includes a required, unique `source_id`. The `asteroid_key` column is unique and references `asteroids.asteroid_key`, allowing at most one orbit record per asteroid in this model.

#### `approaches`

Stores close-approach events, including:

- Close-approach date and epoch timestamp.
- Relative velocity in kilometres per second.
- Miss distance in kilometres.
- Orbiting body.
- Retrieval timestamp.

The table uses a composite primary key consisting of `asteroid_key` and `epoch_date_close_approach`. Its `asteroid_key` references `asteroids.asteroid_key`, allowing multiple approach events for the same asteroid.

### Keys, Constraints, and Relationships

The schema defines foreign key relationships between `asteroids`, `orbits`, and `approaches`.

All three tables use SQLite `STRICT` mode. Required identifiers and retrieval timestamps are declared `NOT NULL`. The asteroid status fields are constrained to `0`, `1`, or `NULL`.

The schema is defined in `sql/schema.sql`. It uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` statements so that initialization can be repeated without recreating existing tables and indexes.

### Database Connection and Initialization

The file `src/db.py` provides the shared database connection and initialization functions.

The `connect()` function opens a SQLite connection and enables foreign key enforcement using `PRAGMA foreign_keys = ON`.

The `initialize_database()` function creates the database directory if necessary and executes the schema.

To initialize the database from the repository root, run:

```bash
python src/db.py
```

The generated database is stored at `data/asteroids.db`. It is a local build artifact and should not be committed to Git.

### Initial Schema Validation

The initial schema was tested using an in-memory SQLite database. The three tables were created successfully, and the foreign key definitions, `STRICT` table declarations, required retrieval timestamp columns, and key constraints were inspected.

The schema initialization command also completed successfully:

```bash
python src/db.py
```

Data loading, validation, quarantine handling, idempotence, atomicity, and analytical query checks must be completed and verified as part of the remaining M2 work.

---

## Planned Analysis

In a later project stage, the asteroid, orbit, and close-approach data will be joined using the asteroid ID.

The analysis will compare potentially hazardous and non-hazardous asteroids and investigate associations between the hazard label and orbital or close-approach characteristics.

Absolute magnitude (H), minimum orbit intersection distance (MOID), and diameter will be excluded from predictive features, as specified in the project proposal.

Because potentially hazardous asteroids may be less common than non-hazardous asteroids, model evaluation will emphasize recall and PR-AUC rather than accuracy alone.

The objective is to investigate associations with a screening label, not to forecast asteroid impacts.

---

## Team

- **Rana Yalçın** — `@se-220717030`
- **Burak Avşar** — `@se-220717054`
- **Elif Şahin** — `@se-230717060`

---

## Status

**M1 — ingestion complete.**

**M2 — database schema and connection setup implemented and tested.** Data loading, validation, integrity checks, and analytical query validation remain to be completed and verified.
