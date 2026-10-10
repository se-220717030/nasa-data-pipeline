# Data Sources

## 1. NASA Near Earth Object Web Service (NeoWs)

- **source_name:** NASA NeoWs (Asteroid Feed & Orbit)
- **provider:** NASA Open APIs / Center for Near Earth Object Studies (CNEOS)
- **url:** https://api.nasa.gov/#asteroids-neows
- **access_method:** REST API, API key required (`NASA_API_KEY`)
- **licence:** Public Domain / NASA API Terms of Use
- **terms_notes:** Free public access under standard NASA API rate limits. Data can be stored locally for analysis.
- **update_cadence:** Weekly (feed updates with new close approaches)
- **coverage:** Historical and upcoming asteroid close approaches and orbital elements.
- **record_meaning:** One row/record represents an asteroid's close approach event or orbital parameters mapped by asteroid ID.
- **join_key:** `id` (Asteroid ID joins the feed/approach data to the orbit data table).
- **first_retrieved:** 2026-10-12
- **known_issues:** High volume of nested JSON structures, pagination required for large ranges, and limited hazardous asteroid counts compared to safe ones.
