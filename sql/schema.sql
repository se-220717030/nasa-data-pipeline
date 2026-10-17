-- NASA Near-Earth Asteroid Data Pipeline
-- M2: Database schema
-- SQLite version 3.37.0+ (STRICT tables)

PRAGMA foreign_keys = ON;

-- 1. Asteroid entities
CREATE TABLE IF NOT EXISTS asteroids (
    asteroid_key INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,
    name TEXT,
    designation TEXT,
    absolute_magnitude_h REAL,
    is_potentially_hazardous INTEGER
        CHECK (
            is_potentially_hazardous IS NULL
            OR is_potentially_hazardous IN (0, 1)
        ),
    is_sentry_object INTEGER
        CHECK (
            is_sentry_object IS NULL
            OR is_sentry_object IN (0, 1)
        ),
    diameter_min_km REAL,
    diameter_max_km REAL,
    retrieved_at TEXT NOT NULL
) STRICT;


-- 2. Orbital data
-- An asteroid may have no orbital data in the collected files.
-- source_id is the NASA asteroid identifier.
CREATE TABLE IF NOT EXISTS orbits (
    orbit_key INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,
    asteroid_key INTEGER NOT NULL UNIQUE,
    eccentricity REAL,
    inclination REAL,
    semi_major_axis REAL,
    orbital_period REAL,
    minimum_orbit_intersection REAL,
    ascending_node_longitude REAL,
    perihelion_argument REAL,
    perihelion_distance REAL,
    aphelion_distance REAL,
    mean_anomaly REAL,
    mean_motion REAL,
    orbit_class_type TEXT,
    orbit_class_description TEXT,
    orbit_class_range TEXT,
    orbit_uncertainty TEXT,
    orbit_determination_date TEXT,
    retrieved_at TEXT NOT NULL,

    FOREIGN KEY (asteroid_key)
        REFERENCES asteroids (asteroid_key)
) STRICT;


-- 3. Close-approach events
-- One event is identified by asteroid + epoch timestamp.
CREATE TABLE IF NOT EXISTS approaches (
    asteroid_key INTEGER NOT NULL,
    epoch_date_close_approach INTEGER NOT NULL,
    close_approach_date TEXT NOT NULL,
    close_approach_date_full TEXT,
    relative_velocity_km_s REAL,
    miss_distance_km REAL,
    orbiting_body TEXT,
    retrieved_at TEXT NOT NULL,

    PRIMARY KEY (
        asteroid_key,
        epoch_date_close_approach
    ),

    FOREIGN KEY (asteroid_key)
        REFERENCES asteroids (asteroid_key)
) STRICT;


-- Indexes for common joins and date-based analysis
CREATE INDEX IF NOT EXISTS idx_approaches_date
    ON approaches (close_approach_date);

CREATE INDEX IF NOT EXISTS idx_approaches_asteroid
    ON approaches (asteroid_key);