# App/common/services/geocoding.py
import requests
from django.conf import settings

class GeocodingError(Exception):
    pass

def _get_base_and_headers():
    base = getattr(settings, "EXTERNAL_GEO", {}).get("NOMINATIM_BASE") or "https://nominatim.openstreetmap.org/search"
    ua   = getattr(settings, "EXTERNAL_GEO", {}).get("USER_AGENT") or "ToolingoApp/1.0 (contacto@example.com)"
    timeout = getattr(settings, "HTTP_CLIENT_TIMEOUT", 8)
    headers = {"User-Agent": ua}
    return base, headers, timeout

def geocode_city(city_name: str, country_codes: str | None = None) -> tuple[float, float]:
    """
    Resuelve nombre de ciudad -> (lat, lon)
    """
    base, headers, timeout = _get_base_and_headers()
    params = {
        "q": city_name,
        "format": "jsonv2",
        "limit": 1,
    }
    if country_codes:
        params["countrycodes"] = country_codes  # ej: "co"

    try:
        resp = requests.get(base, headers=headers, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise GeocodingError(f"Error consultando Nominatim: {e}") from e

    if not data:
        raise GeocodingError(f"No se encontró la ciudad: {city_name}")

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    return (lat, lon)

def geocode_address(address: str, country_codes: str | None = None) -> tuple[float, float, str]:
    """
    Resuelve una dirección libre -> (lat, lon, display_name)
    """
    base, headers, timeout = _get_base_and_headers()
    params = {
        "q": address,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 0,
    }
    if country_codes:
        params["countrycodes"] = country_codes

    try:
        resp = requests.get(base, headers=headers, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise GeocodingError(f"Error consultando Nominatim: {e}") from e

    if not data:
        raise GeocodingError(f"No se encontró la dirección: {address}")

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    display = data[0].get("display_name", address)
    return (lat, lon, display)
