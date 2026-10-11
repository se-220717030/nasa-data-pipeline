# NASA Near-Earth Asteroid Hazard Analysis

## Project Question

**Which asteroid features are linked to a “potentially hazardous” label?**

This project uses NASA's Near Earth Object Web Service (NeoWs) to collect data about near-Earth asteroids, their orbital characteristics, and close approaches. We will join asteroid, orbit, and close-approach data using the asteroid ID and compare potentially hazardous and non-hazardous asteroids.

The project will investigate which orbital and close-approach features are associated with the potentially hazardous label. A simple classifier will be developed in a later stage of the project. Since the hazard label is built from absolute magnitude (H) and minimum orbit intersection distance (MOID), H, MOID, and diameter will not be used as model features. The hazard label is treated as a screening label, not an impact forecast.

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

### Planned Data Entities

The collected data will support the following entities:

- **asteroids** — one row per asteroid.
- **orbits** — one row per asteroid orbit.
- **approaches** — one row per close approach.

The common join key is the **asteroid ID**.

The initial data collection target is at least 5,000 asteroids and their associated close approaches.

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

```bash
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

The script is expected to retrieve data from the approved NASA NeoWs endpoints and save the raw responses in `data/raw/`.

Each run must preserve the original responses and use UTC retrieval timestamps in filenames. Subsequent runs must create new files rather than overwrite previously retrieved files.

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
├── src/
│   └── ingest.py
└── docs/
    └── sources.md
```

### Directory and File Descriptions

| Path | Description |
|---|---|
| `README.md` | Project overview and instructions |
| `.gitignore` | Specifies files and directories Git should ignore |
| `.env.example` | Documents the required environment variables |
| `requirements.txt` | Lists the required Python dependencies |
| `data/raw/` | Stores raw data retrieved during ingestion |
| `src/ingest.py` | Contains the NASA NeoWs ingestion script |
| `docs/sources.md` | Documents data sources and provenance |

---

## Ingestion Scope — M1

Milestone M1 focuses on the ingestion stage of the data engineering lifecycle.

The ingestion script is expected to:

1. Retrieve data from the approved NASA NeoWs sources.
2. Save raw responses without cleaning, filtering, renaming, or reshaping them.
3. Include UTC retrieval timestamps in saved filenames.
4. Create new files on subsequent runs without overwriting previous files.
5. Read credentials from environment variables.
6. Handle request failures, timeouts, rate limits, and server errors appropriately.
7. Report the retrieved sources, record or file counts, and any errors.

Data cleaning, transformation, feature engineering, database loading, and machine learning are outside the scope of M1.

---

## Planned Analysis

In a later project stage, the collected asteroid, orbit, and close-approach data will be connected using the asteroid ID.

The project will compare potentially hazardous and non-hazardous asteroids and investigate associations between the hazard label and orbital or close-approach characteristics.

Absolute magnitude (H), MOID, and diameter will be excluded from the predictive features, as specified in the project proposal.

Because hazardous asteroids may be less common than non-hazardous asteroids, model evaluation will emphasize recall and PR-AUC rather than accuracy alone.

The objective is to investigate associations with a screening label, not to forecast asteroid impacts.

---

## Team

- **Rana Yalçın** — `@se-220717030`
- **Burak Avşar** — `@se-220717054`
- **Elif Şahin** — `@se-230717060`

## Status

M1 — ingestion complete