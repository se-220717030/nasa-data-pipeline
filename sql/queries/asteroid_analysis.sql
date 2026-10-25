-- Question: How do potentially hazardous asteroids differ from non-hazardous ones
--           in their orbits and in their close approaches to Earth?
--
-- Result grain: one row per value of asteroids.is_potentially_hazardous (1 = hazardous, 0 = not).
--
-- Why the aggregation is correct at this grain:
--   approaches has many rows per asteroid (one per close approach), orbits has at most one.
--   Joining approaches straight onto asteroids and then averaging would weight every asteroid
--   by its number of approaches, and COUNT(*) would count approaches instead of asteroids.
--   So the CTE first collapses approaches to ONE row per asteroid (Earth approaches only),
--   and only then is it LEFT JOINed to asteroids and orbits. After the joins every row is still
--   one asteroid, so COUNT(*) counts asteroids and each AVG gives every asteroid equal weight.
--   LEFT JOINs keep asteroids without an orbit or without an Earth approach; AVG skips their NULLs,
--   and the n_with_* columns show how many asteroids each average is based on.
--   H, MOID and diameter define the hazard label, so they are deliberately left out.

WITH earth_approaches AS (          -- grain: one row per asteroid
    SELECT
        asteroid_key,
        COUNT(*)                    AS n_approaches,
        MIN(miss_distance_km)       AS closest_miss_km,
        MAX(relative_velocity_km_s) AS fastest_km_s
    FROM approaches
    WHERE orbiting_body = 'Earth'
    GROUP BY asteroid_key
)
SELECT
    a.is_potentially_hazardous                       AS hazardous,
    COUNT(*)                                         AS n_asteroids,
    COUNT(o.asteroid_key)                            AS n_with_orbit,
    ROUND(AVG(o.eccentricity), 3)                    AS avg_eccentricity,
    ROUND(AVG(o.inclination), 1)                     AS avg_inclination_deg,
    ROUND(AVG(o.semi_major_axis), 2)                 AS avg_semi_major_axis_au,
    COUNT(e.asteroid_key)                            AS n_with_earth_approach,
    ROUND(AVG(e.n_approaches), 1)                    AS avg_earth_approaches,
    ROUND(AVG(e.closest_miss_km) / 1e6, 2)           AS avg_closest_miss_million_km,
    ROUND(AVG(e.fastest_km_s), 1)                    AS avg_fastest_km_s
FROM asteroids AS a
LEFT JOIN orbits AS o           ON o.asteroid_key = a.asteroid_key
LEFT JOIN earth_approaches AS e ON e.asteroid_key = a.asteroid_key
GROUP BY a.is_potentially_hazardous
ORDER BY hazardous DESC;
