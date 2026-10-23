"""
FloodSentinel AI live data adapters and historical CSV audit helpers.

Live weather: Open-Meteo (model-derived weather, not an official IMD observation).
Official alerts: NDMA SACHET public India CAP RSS feed.
CWC/NWIC river and Maharashtra WRD reservoir feeds are intentionally not guessed:
they return unavailable until a verified endpoint/download access method is configured.

Usage:
    from data_sources import fetch_live_weather, fetch_ndma_alerts, audit_historical_csv
    print(fetch_live_weather("Kolhapur"))
    print(fetch_live_weather("Sangli"))
"""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlencode
import csv
import io
import json
import os
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

WEATHER_LOCATIONS = {
    "Kolhapur": {"latitude": 16.7050, "longitude": 74.2433},
    "Sangli": {"latitude": 16.8524, "longitude": 74.5815},
}
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
NDMA_CAP_RSS_URL = "https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml"
DEFAULT_TIMEOUT_SECONDS = 12


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _record(
    *,
    source: str,
    metric: str,
    location: str,
    value: Any = None,
    unit: str | None = None,
    observation_time: str | None = None,
    retrieval_time: str | None = None,
    status: str = "ok",
    source_url: str | None = None,
    details: str | None = None,
) -> dict[str, Any]:
    """Return a consistent, JSON-serializable observation envelope."""
    return {
        "source": source,
        "metric": metric,
        "location": location,
        "value": value,
        "unit": unit,
        "observation_time": observation_time,
        "retrieval_time": retrieval_time or _now_utc(),
        "status": status,
        "source_url": source_url,
        "details": details,
    }


def _get_json(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FloodSentinelAI/0.1 (data quality; contact project maintainer)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def fetch_live_weather(location: str = "Kolhapur") -> dict[str, Any]:
    """
    Fetch current modelled weather and latest hourly precipitation from Open-Meteo.
    No API key is required for ordinary non-commercial use; observe provider terms.
    Returns status='unavailable' or 'error' instead of fabricated values.
    """
    retrieval_time = _now_utc()
    coords = WEATHER_LOCATIONS.get(location)
    if coords is None:
        return {
            "source": "Open-Meteo",
            "location": location,
            "retrieval_time": retrieval_time,
            "status": "unavailable",
            "observations": [],
            "details": f"Unknown location. Choose one of: {', '.join(WEATHER_LOCATIONS)}.",
        }

    params = {
        **coords,
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,showers,wind_speed_10m",
        "hourly": "precipitation",
        "forecast_days": 1,
        "timezone": "Asia/Kolkata",
    }
    url = OPEN_METEO_URL + "?" + urlencode(params)
    try:
        payload = _get_json(url)
        current = payload.get("current") or {}
        units = payload.get("current_units") or {}
        observed_at = current.get("time")
        mapping = [
            ("temperature_2m", "temperature", "°C"),
            ("relative_humidity_2m", "relative_humidity", "%"),
            ("precipitation", "precipitation", "mm"),
            ("rain", "rain", "mm"),
            ("showers", "showers", "mm"),
            ("wind_speed_10m", "wind_speed", "km/h"),
        ]
        observations = []
        for api_key, metric, fallback_unit in mapping:
            value = current.get(api_key)
            if value is None:
                observations.append(_record(
                    source="Open-Meteo", metric=metric, location=location,
                    observation_time=observed_at, retrieval_time=retrieval_time,
                    status="unavailable", source_url=url,
                    details=f"API response did not contain {api_key}.",
                    unit=units.get(api_key, fallback_unit),
                ))
            else:
                observations.append(_record(
                    source="Open-Meteo", metric=metric, location=location,
                    value=value, unit=units.get(api_key, fallback_unit),
                    observation_time=observed_at, retrieval_time=retrieval_time,
                    status="ok", source_url=url,
                    details="Model-derived weather estimate; not an official IMD station observation.",
                ))
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        precip = hourly.get("precipitation") or []
        if times and precip:
            latest_idx = min(len(times), len(precip)) - 1
            # The most recent hourly slot is returned separately; this is not assumed to be an observed gauge total.
            observations.append(_record(
                source="Open-Meteo", metric="hourly_precipitation",
                location=location, value=precip[latest_idx], unit="mm",
                observation_time=times[latest_idx], retrieval_time=retrieval_time,
                status="ok" if precip[latest_idx] is not None else "unavailable",
                source_url=url,
                details="Hourly modelled precipitation slot; inspect time field before interpreting as observed rainfall.",
            ))
        return {
            "source": "Open-Meteo",
            "location": location,
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "retrieval_time": retrieval_time,
            "status": "ok" if any(x["status"] == "ok" for x in observations) else "unavailable",
            "observations": observations,
            "source_url": url,
            "attribution": "Open-Meteo; see https://open-meteo.com/en/terms",
        }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        return {
            "source": "Open-Meteo",
            "location": location,
            "retrieval_time": retrieval_time,
            "status": "unavailable",
            "observations": [],
            "source_url": url,
            "details": f"Live request failed: {type(exc).__name__}: {exc}",
        }


def fetch_ndma_alerts(timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """
    Read the publicly documented India CAP RSS feed from NDMA SACHET.
    The feed is nationwide; returned items are not automatically filtered to Kolhapur/Sangli.
    """
    retrieved = _now_utc()
    req = urllib.request.Request(
        NDMA_CAP_RSS_URL,
        headers={"User-Agent": "FloodSentinelAI/0.1", "Accept": "application/rss+xml, application/xml"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read()
        root = ET.fromstring(body)
        items = []
        for item in root.findall(".//item"):
            title = item.findtext("title")
            link = item.findtext("link")
            description = item.findtext("description")
            pub_date = item.findtext("pubDate")
            try:
                obs_time = parsedate_to_datetime(pub_date).astimezone(timezone.utc).isoformat() if pub_date else None
            except (TypeError, ValueError, OverflowError):
                obs_time = pub_date
            items.append({
                "source": "NDMA SACHET India CAP RSS",
                "title": title,
                "description": description,
                "url": link,
                "observation_time": obs_time,
                "retrieval_time": retrieved,
                "unit": None,
                "status": "ok",
            })
        return {
            "source": "NDMA SACHET India CAP RSS",
            "retrieval_time": retrieved,
            "status": "ok",
            "count": len(items),
            "alerts": items,
            "source_url": NDMA_CAP_RSS_URL,
            "details": "Nationwide feed. Confirm geography, validity period, and issuer before using an alert operationally.",
        }
    except (urllib.error.URLError, TimeoutError, OSError, ET.ParseError) as exc:
        return {
            "source": "NDMA SACHET India CAP RSS",
            "retrieval_time": retrieved,
            "status": "unavailable",
            "count": 0,
            "alerts": [],
            "source_url": NDMA_CAP_RSS_URL,
            "details": f"Feed request/parse failed: {type(exc).__name__}: {exc}",
        }


def unavailable_hydrology_source(source: str, location: str, metric: str, reason: str) -> dict[str, Any]:
    """
    Honest placeholder for river gauges/reservoirs until an exact, authorized data endpoint
    or downloadable file for the required station is configured.
    """
    return _record(
        source=source, metric=metric, location=location, value=None, unit=None,
        observation_time=None, status="unavailable",
        source_url=None, details=reason,
    )


def fetch_river_gauge(location: str = "Kolhapur") -> dict[str, Any]:
    return unavailable_hydrology_source(
        "CWC / National Water Data Portal",
        location,
        "river_water_level",
        "No station-specific live endpoint has been configured or verified for this location. "
        "NWDP lists CWC telemetry datasets and API/CSV resources, but the exact station/resource "
        "and access method must be confirmed before ingestion.",
    )


def fetch_reservoir_data(reservoir: str = "Koyna") -> dict[str, Any]:
    return unavailable_hydrology_source(
        "Maharashtra WRD / NWIC",
        reservoir,
        "reservoir_level_or_storage",
        "No verified public live endpoint for this reservoir has been configured. "
        "Maharashtra WRD dam storage pages and NWIC reservoir telemetry catalogs are discovery "
        "leads, not proof that this reservoir's live series is publicly accessible.",
    )


def audit_historical_csv(path: str, date_column: str = "date") -> dict[str, Any]:
    """
    Basic quality audit for an existing CSV. Does not verify provenance or truth.
    Flags missing cells, duplicate rows, repeated values in numeric columns, bad dates,
    and likely unit/range issues for common rainfall/river-level field names.
    """
    import pandas as pd

    df = pd.read_csv(path, low_memory=False)
    missing_by_column = {str(k): int(v) for k, v in df.isna().sum().items() if int(v) > 0}
    duplicate_rows = int(df.duplicated().sum())
    date_errors = []
    if date_column in df.columns:
        parsed = pd.to_datetime(df[date_column], errors="coerce", dayfirst=True)
        date_errors = [
            {"row_number": int(i) + 2, "value": str(df.iloc[i][date_column])}
            for i in range(len(df)) if pd.isna(parsed.iloc[i])
        ]
        duplicate_dates = int(parsed.dropna().duplicated().sum())
    else:
        duplicate_dates = None
        date_errors = [{"row_number": None, "value": None, "issue": f"Missing date column '{date_column}'"}]

    repeated_numeric = {}
    range_flags = []
    for col in df.columns:
        numeric = pd.to_numeric(df[col], errors="coerce")
        valid = numeric.dropna()
        if len(valid) >= 3:
            repeated_numeric[str(col)] = {
                "unique_values": int(valid.nunique()),
                "valid_values": int(len(valid)),
                "most_common_value_count": int(valid.value_counts().iloc[0]),
            }
        normalized = str(col).lower()
        if "rain" in normalized and len(valid):
            # Negative rainfall is suspicious; >1000 mm per single observation merits review, not automatic rejection.
            bad = (numeric < 0) | (numeric > 1000)
            if bad.any():
                range_flags.append({"column": str(col), "rows_1_based_with_header": [int(i)+2 for i in df.index[bad][:100]], "rule": "rainfall < 0 or > 1000; inspect units/time interval"})
        if ("river_level" in normalized or "water_level" in normalized) and len(valid):
            bad = (numeric < -5) | (numeric > 100)
            if bad.any():
                range_flags.append({"column": str(col), "rows_1_based_with_header": [int(i)+2 for i in df.index[bad][:100]], "rule": "level outside broad -5..100 m sanity screen; confirm station datum/units"})

    return {
        "file": os.path.abspath(path),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": [str(c) for c in df.columns],
        "missing_by_column": missing_by_column,
        "duplicate_full_rows": duplicate_rows,
        "duplicate_parsed_dates": duplicate_dates,
        "invalid_dates": date_errors,
        "numeric_repetition_summary": repeated_numeric,
        "range_flags": range_flags,
        "provenance_status": "not_verified",
        "limitations": [
            "Repeated readings can be legitimate; this report flags patterns but does not label them erroneous.",
            "Range screens are broad heuristics, not station-specific hydrological validation.",
            "A CSV quality audit cannot verify a value against IMD/CWC/WRD source records.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps({
        "weather_kolhapur": fetch_live_weather("Kolhapur"),
        "weather_sangli": fetch_live_weather("Sangli"),
        "ndma_alerts": fetch_ndma_alerts(),
        "river_gauge_kolhapur": fetch_river_gauge("Kolhapur"),
        "reservoir_koyna": fetch_reservoir_data("Koyna"),
    }, indent=2, ensure_ascii=False))
