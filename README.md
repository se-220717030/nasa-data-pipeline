# NASA Near-Earth Asteroid Hazard Analysis

## Project Question

**Which asteroid features are linked to a “potentially hazardous” label?**

This project uses NASA's Near Earth Object Web Service (NeoWs) to collect
data about near-Earth asteroids, their orbital characteristics, and close
approaches. We will join asteroid, orbit, and close-approach data using the
asteroid ID and compare potentially hazardous and non-hazardous asteroids.

The project will investigate which orbit and approach features are associated
with the potentially hazardous label. A simple classifier will be trained in
a later stage of the project. Since the hazard label is built from absolute
magnitude (H) and minimum orbit intersection distance (MOID), H, MOID, and
diameter will not be used as model features. The hazard label is treated as
a screening label, not an impact forecast.

---

## Data Sources

### NASA Near Earth Object Web Service (NeoWs)

The primary data source is NASA's Near Earth Object Web Service (NeoWs),
a public REST API that provides JSON data about near-Earth asteroids.

The project uses the following NeoWs endpoints:

- **Browse** — provides the asteroid catalogue.
- **Feed** — provides close-approach data for a specified date range.
- **Lookup** — provides detailed information for an individual asteroid.

Official NASA API documentation:

https://api.nasa.gov/#asteroids-neows

Detailed source and provenance information is available in:

[`docs/sources.md`](docs/sources.md)

The API requires a NASA API key. The key is provided through an environment
variable and must not be committed to the repository.

### Planned Data Entities

The data collected from NeoWs will support the following entities:

- **asteroids** — one row per asteroid.
- **orbits** — one row per asteroid orbit.
- **approaches** — one row per close approach.

The common join key is the **asteroid ID**.

The project will initially retrieve at least 5,000 asteroids and their
associated close approaches.

---

## How to Run

### 1. Clone the repository

```bash
git clone <REPOSITORY_URL>
cd <REPOSITORY_NAME>