# FloodSentinel AI — live data sources and verification

Last reviewed: 2026-10-23. This document distinguishes source discovery from a verified working feed.

## Implemented adapters

### Open-Meteo weather and precipitation
- Endpoint: `https://api.open-meteo.com/v1/forecast`
- Data: current modelled temperature, humidity, precipitation/rain/showers, wind speed, plus a precipitation hourly slot.
- Access: no API key for ordinary non-commercial use; review current terms, attribution and rate limits before production.
- Update cadence: provider model updates; API output is current-model data, not guaranteed to be a live rain gauge.
- Locations: Kolhapur (16.7050, 74.2433) and Sangli (16.8524, 74.5815).
- Status semantics: `ok` means the request returned a field, not that an official station confirmed it.
- Docs: https://open-meteo.com/en/docs
- Terms: https://open-meteo.com/en/terms

### NDMA SACHET India CAP RSS
- Feed: `https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml`
- The NDMA SACHET portal describes an India CAP RSS feed and near-real-time geo-targeted public alerts. The adapter parses RSS item title, description, URL and publication time.
- Access: public RSS feed is listed by the WMO Register of Alerting Authorities; no API key documented for the RSS URL. Availability and schema may change.
- Update cadence: event-driven alert publication; not a fixed polling guarantee.
- Important: feed is nationwide. Filter and verify each alert's district/validity/issuer before presenting it as relevant to Kolhapur or Sangli.
- Sources: https://sachet.ndma.gov.in/CapFeed and https://alertingauthority.wmo.int/authorities.php?recId=331

## Official hydrology sources discovered; live adapter not yet verified

### CWC / National Water Data Portal (NWIC)
- The portal catalogs CWC hourly telemetry datasets for river water level and discharge and describes CSV/API resources.
- Dataset discovery page: https://nwdp.nwic.gov.in/en/dataset/river-water-level-telemetry-hourly-central-water-commission-cwc
- Discharge catalog: https://nwdp.nwic.gov.in/dataset/river-discharge-telemetry-hourly-central-water-commission-cwc
- CWC rainfall catalog: https://nwdp.nwic.gov.in/en/dataset/rainfall-cwc-telemetry-hourly
- Access: some catalogued resources show CSV/API, but this does not prove that a specific Krishna/Panchganga station, latest period, and public endpoint are available without credentials. Identify the exact station/resource and test its download/API terms before enabling ingestion.
- Update cadence: dataset metadata advertises hourly telemetry for relevant datasets; actual freshness must be checked per resource.
- Current code: `fetch_river_gauge()` returns `unavailable` rather than inventing a level.

### Maharashtra Water Resources Department (WRD) / dam storage
- Public discovery page: https://mahahp.gov.in/DamDataDisplay.aspx (says water-storage source is WRD).
- WRD portal: https://wrd.mahaonline.gov.in/
- NWIC also catalogs some Maharashtra reservoir telemetry, but a generic catalog is not proof of live Koyna, Radhanagari, or Warna data access.
- Access: public page/download availability and permission requirements must be confirmed for each reservoir/station; some hydrological data can be subject to a formal data request.
- Current code: `fetch_reservoir_data()` returns `unavailable` until a specific verified source is configured.

### India Meteorological Department (IMD)
- Official API reference lists current weather, station nowcast, district rainfall, warnings, and other APIs: https://api.imd.gov.in/public/api_reference.html
- Registration portal: https://api.imd.gov.in/public/register.php
- Access: account registration is available; exact API entitlement, key/token, terms and endpoints must be confirmed for the intended dataset. IMD should be preferred for official rainfall/weather warnings when authorized access is configured.
- Current implementation uses Open-Meteo for the first working weather adapter, not as a substitute for official IMD station observations.

## Common record format
Every observation includes:
`source`, `metric`, `location`, `value`, `unit`, `observation_time`, `retrieval_time`, `status`, `source_url`, `details`.
Status values currently include `ok` and `unavailable`. A returned weather field is modelled weather; it is not independently verified as an official station observation.

## Historical CSV audit
Call `audit_historical_csv("path/to/file.csv")`. It reports missing cells, duplicate full rows, duplicate parsed dates, invalid dates, repeated-value patterns and broad range flags. It does **not** establish provenance or truth. Compare rainfall with IMD, river levels/discharge with CWC/NWIC, and dam operations/storage with Maharashtra WRD records for matching station, timestamp, unit and datum.

The August 2019 dataset discussed in the project was described as transcribed/analysis-ready but still requiring verification. The actual CSV/workbook and source citations were not attached to this task, so no claims are made here about its specific missing cells or value accuracy.

## Run
```bash
python -m pip install -r requirements.txt
python data_sources.py
```
Successful live values are printed only when the endpoint actually responds. If networking is blocked, the output records `unavailable` with an error detail. Never replace unavailable readings with demo/sample values.

## Secret handling
- No API key is needed by the implemented Open-Meteo public endpoint or NDMA RSS feed as currently configured.
- Do not commit `.env` or tokens. If an authenticated IMD/NWIC/WRD integration is later added, load credentials from environment variables and add `.env` to `.gitignore`.
