-- Question: how close does each asteroid come to Earth, by hazard label? (cleaned layer)
-- Grain: one row per resolved asteroid that has at least one Earth approach.
-- Flag filter (parameters):
--   identity_flag = 'ok'                     duplicate NASA ids counted once (their approaches are the same events)
--   is_potentially_hazardous IS NOT NULL     label present (label_rule_mismatch rows kept unless :exclude_label_mismatch = 1)
--   miss_distance_km IS NOT NULL             drops missing_* and invalid_* values
--   miss_distance_km_flag = 'ok'             unless :include_unusual = 1 (then unusual_low / unusual_high count too)
--   timing_flag = 'past'                     unless :include_predicted = 1
SELECT
    c.asteroid_key,
    c.is_potentially_hazardous AS hazardous,
    MIN(p.miss_distance_km)    AS closest_km,
    COUNT(*)                   AS n_earth_approaches
FROM asteroid_clean AS c
JOIN approach_clean AS p ON p.asteroid_key = c.asteroid_key
WHERE p.orbiting_body = 'Earth'
  AND c.identity_flag = 'ok'
  AND c.is_potentially_hazardous IS NOT NULL
  AND (c.is_potentially_hazardous_flag <> 'label_rule_mismatch' OR :exclude_label_mismatch = 0)
  AND p.miss_distance_km IS NOT NULL
  AND (p.miss_distance_km_flag = 'ok' OR :include_unusual = 1)
  AND (p.timing_flag = 'past' OR :include_predicted = 1)
GROUP BY c.asteroid_key, c.is_potentially_hazardous;
