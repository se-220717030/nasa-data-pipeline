-- Question: how close does each asteroid come to Earth, by hazard label? (raw M2 tables, as loaded)
-- Grain: one row per asteroid that has at least one Earth approach.
-- Flag filter: none (M2 tables have no flags); every asteroid row counts, including duplicate NASA ids.
SELECT
    a.asteroid_key,
    a.is_potentially_hazardous AS hazardous,
    MIN(p.miss_distance_km)    AS closest_km,
    COUNT(*)                   AS n_earth_approaches
FROM asteroids AS a
JOIN approaches AS p ON p.asteroid_key = a.asteroid_key
WHERE p.orbiting_body = 'Earth'
GROUP BY a.asteroid_key, a.is_potentially_hazardous;
