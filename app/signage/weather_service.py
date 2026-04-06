from __future__ import annotations

import hashlib
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


def _weather_settings() -> dict:
    defaults = {
        "REFRESH_INTERVAL_SECONDS": 900,
        "STALE_TTL_SECONDS": 21600,
        "HTTP_TIMEOUT_SECONDS": 5,
        "FORECAST_DAYS": 5,
    }
    raw = getattr(settings, "WEATHER_WIDGET", {})
    if isinstance(raw, dict):
        defaults.update(raw)
    return defaults


def _normalize_units(raw_units: str | None) -> tuple[str, str]:
    value = (raw_units or "celsius").strip().lower()
    if value in {"f", "fahrenheit", "imperial"}:
        return "fahrenheit", "imperial"
    return "celsius", "metric"


def _build_cache_key(location: str, units: str) -> str:
    digest = hashlib.sha256(f"{location}|{units}".encode("utf-8")).hexdigest()
    return f"weather_widget:{digest}"


def _parse_dt(value):
    if not value:
        return None
    try:
        return timezone.datetime.fromisoformat(str(value))
    except Exception:
        return None


def _make_snapshot_payload(location: str, ui_units: str, weather_json: dict, forecast_json: dict, forecast_days: int) -> dict:
    weather_main = weather_json.get("main", {}) if isinstance(weather_json, dict) else {}
    weather_desc = (weather_json.get("weather") or [{}])[0] if isinstance(weather_json, dict) else {}

    city = weather_json.get("name") or location
    sys_data = weather_json.get("sys", {}) if isinstance(weather_json, dict) else {}
    country = sys_data.get("country")
    location_label = f"{city}, {country}" if country and city else city

    # OpenWeather forecast is 3-hourly; pick one item per day for a glanceable strip.
    daily_rows = []
    seen_days = set()
    for item in (forecast_json.get("list") or []):
        dt_txt = str(item.get("dt_txt") or "")
        day_key = dt_txt.split(" ")[0] if " " in dt_txt else dt_txt[:10]
        if not day_key or day_key in seen_days:
            continue
        seen_days.add(day_key)
        main = item.get("main", {})
        weather_item = (item.get("weather") or [{}])[0]
        daily_rows.append(
            {
                "date": day_key,
                "temp_min": main.get("temp_min"),
                "temp_max": main.get("temp_max"),
                "description": weather_item.get("description"),
                "icon": weather_item.get("icon"),
            }
        )
        if len(daily_rows) >= max(1, int(forecast_days or 5)):
            break

    return {
        "updated_at": timezone.now().isoformat(),
        "location": {
            "query": location,
            "label": location_label,
            "timezone_offset_seconds": weather_json.get("timezone"),
        },
        "units": ui_units,
        "current": {
            "temp": weather_main.get("temp"),
            "temp_min": weather_main.get("temp_min"),
            "temp_max": weather_main.get("temp_max"),
            "feels_like": weather_main.get("feels_like"),
            "description": weather_desc.get("description"),
            "icon": weather_desc.get("icon"),
        },
        "forecast": daily_rows,
    }


def _fetch_openweather(location: str, provider_units: str, timeout_seconds: int, forecast_days: int) -> dict:
    api_key = getattr(settings, "OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENWEATHER_API_KEY is not configured")

    base_url = getattr(settings, "OPENWEATHER_BASE_URL", "https://api.openweathermap.org").rstrip("/")
    params = {"q": location, "appid": api_key, "units": provider_units}

    weather_resp = requests.get(f"{base_url}/data/2.5/weather", params=params, timeout=timeout_seconds)
    weather_resp.raise_for_status()
    weather_json = weather_resp.json()

    forecast_resp = requests.get(f"{base_url}/data/2.5/forecast", params=params, timeout=timeout_seconds)
    forecast_resp.raise_for_status()
    forecast_json = forecast_resp.json()

    return _make_snapshot_payload(location, "fahrenheit" if provider_units == "imperial" else "celsius", weather_json, forecast_json, forecast_days)


def _open_meteo_code_to_icon(code: int | None, is_day: int | None) -> str:
    # Map Open-Meteo weather codes to OpenWeather-like icon ids for existing UI rendering.
    mapping = {
        0: "01",
        1: "02",
        2: "03",
        3: "04",
        45: "50",
        48: "50",
        51: "09",
        53: "09",
        55: "09",
        56: "13",
        57: "13",
        61: "10",
        63: "10",
        65: "10",
        66: "13",
        67: "13",
        71: "13",
        73: "13",
        75: "13",
        77: "13",
        80: "09",
        81: "09",
        82: "09",
        85: "13",
        86: "13",
        95: "11",
        96: "11",
        99: "11",
    }
    base = mapping.get(int(code) if code is not None else -1, "03")
    suffix = "d" if int(is_day or 1) == 1 else "n"
    return f"{base}{suffix}"


def _fetch_open_meteo(location: str, ui_units: str, timeout_seconds: int, forecast_days: int) -> dict:
    # Parse "City,CC" patterns while still supporting plain city names.
    query = str(location or "").strip()
    if not query:
        raise RuntimeError("Weather location is empty")
    parts = [p.strip() for p in query.split(",") if p.strip()]
    city_name = parts[0]
    country_code = parts[1].upper() if len(parts) > 1 else None

    geocode_resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city_name, "count": 10, "language": "en", "format": "json"},
        timeout=timeout_seconds,
    )
    geocode_resp.raise_for_status()
    geo_json = geocode_resp.json() or {}
    results = geo_json.get("results") or []
    if not results:
        raise RuntimeError(f"No geocoding result for '{query}'")

    selected = results[0]
    if country_code:
        for row in results:
            if str(row.get("country_code", "")).upper() == country_code:
                selected = row
                break

    lat = selected.get("latitude")
    lon = selected.get("longitude")
    if lat is None or lon is None:
        raise RuntimeError(f"Invalid geocoding coordinates for '{query}'")

    temp_unit = "fahrenheit" if ui_units == "fahrenheit" else "celsius"
    wind_unit = "mph" if ui_units == "fahrenheit" else "kmh"
    forecast_resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code,is_day",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "timezone": "auto",
            "temperature_unit": temp_unit,
            "wind_speed_unit": wind_unit,
            "forecast_days": max(3, min(7, int(forecast_days or 5))),
        },
        timeout=timeout_seconds,
    )
    forecast_resp.raise_for_status()
    data = forecast_resp.json() or {}
    current = data.get("current") or {}
    daily = data.get("daily") or {}
    days = daily.get("time") or []
    mins = daily.get("temperature_2m_min") or []
    maxs = daily.get("temperature_2m_max") or []
    codes = daily.get("weather_code") or []

    forecast_rows = []
    for idx, day in enumerate(days[: max(1, int(forecast_days or 5))]):
        code = codes[idx] if idx < len(codes) else None
        forecast_rows.append(
            {
                "date": day,
                "temp_min": mins[idx] if idx < len(mins) else None,
                "temp_max": maxs[idx] if idx < len(maxs) else None,
                "description": "",
                "icon": _open_meteo_code_to_icon(code, 1),
            }
        )

    current_code = current.get("weather_code")
    current_is_day = current.get("is_day", 1)
    location_label = selected.get("name") or query
    if selected.get("country_code"):
        location_label = f"{location_label}, {selected.get('country_code')}"

    return {
        "updated_at": timezone.now().isoformat(),
        "location": {
            "query": query,
            "label": location_label,
            "timezone_offset_seconds": None,
        },
        "units": ui_units,
        "current": {
            "temp": current.get("temperature_2m"),
            "temp_min": forecast_rows[0].get("temp_min") if forecast_rows else None,
            "temp_max": forecast_rows[0].get("temp_max") if forecast_rows else None,
            "feels_like": None,
            "description": "",
            "icon": _open_meteo_code_to_icon(current_code, current_is_day),
        },
        "forecast": forecast_rows,
    }


def enrich_weather_style(style_payload: dict) -> dict:
    """
    Inject weather snapshot/meta into widget style payload.
    Returns the original style (with added weather keys when available).
    """
    style = dict(style_payload or {})
    location = str(style.get("location") or "").strip()
    if not location:
        return style

    cfg = _weather_settings()
    refresh_s = max(60, int(style.get("refreshIntervalSeconds") or cfg["REFRESH_INTERVAL_SECONDS"]))
    stale_ttl_s = max(refresh_s, int(style.get("staleTtlSeconds") or cfg["STALE_TTL_SECONDS"]))
    timeout_s = max(2, int(cfg["HTTP_TIMEOUT_SECONDS"]))
    forecast_days = max(1, min(5, int(style.get("forecastDays") or cfg["FORECAST_DAYS"])))
    ui_units, provider_units = _normalize_units(style.get("units"))

    cache_key = _build_cache_key(location, provider_units)
    cached = cache.get(cache_key) or {}
    cached_snapshot = cached.get("snapshot") if isinstance(cached, dict) else None
    cached_updated = _parse_dt(cached_snapshot.get("updated_at")) if isinstance(cached_snapshot, dict) else None

    now = timezone.now()
    can_use_fresh_cache = cached_updated and (now - cached_updated) <= timedelta(seconds=refresh_s)
    if can_use_fresh_cache:
        style["weatherData"] = cached_snapshot
        style["weatherMeta"] = {"source": "cache", "stale": False}
        style["units"] = ui_units
        return style

    try:
        api_key = getattr(settings, "OPENWEATHER_API_KEY", "").strip()
        if api_key:
            snapshot = _fetch_openweather(location, provider_units, timeout_s, forecast_days)
            source = "live-openweather"
        else:
            snapshot = _fetch_open_meteo(location, ui_units, timeout_s, forecast_days)
            source = "live-open-meteo"
        cache.set(cache_key, {"snapshot": snapshot}, timeout=stale_ttl_s)
        style["weatherData"] = snapshot
        style["weatherMeta"] = {"source": source, "stale": False}
        style["units"] = ui_units
        return style
    except Exception as exc:
        if cached_snapshot and cached_updated and (now - cached_updated) <= timedelta(seconds=stale_ttl_s):
            logger.warning("Weather API unavailable; using stale cache for %s: %s", location, exc)
            style["weatherData"] = cached_snapshot
            style["weatherMeta"] = {"source": "cache-stale", "stale": True, "reason": str(exc)}
            style["units"] = ui_units
            return style

        logger.warning("Weather API unavailable and no usable cache for %s: %s", location, exc)
        style["weatherMeta"] = {"source": "unavailable", "stale": True, "reason": str(exc)}
        style["units"] = ui_units
        return style
