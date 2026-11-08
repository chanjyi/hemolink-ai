from __future__ import annotations

import math
from datetime import date, timedelta


def parse(iso: str) -> date:
    return date.fromisoformat(iso[:10])


def add_days(iso: str, days: int) -> str:
    return (parse(iso) + timedelta(days=days)).isoformat()


def days_between(from_iso: str, to_iso: str) -> int:
    return (parse(to_iso) - parse(from_iso)).days


def weekday(iso: str) -> int:
    """0 = Sunday ... 6 = Saturday (same as JavaScript getUTCDay)."""
    return (parse(iso).weekday() + 1) % 7


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def format_date(iso: str) -> str:
    d = parse(iso)
    return f"{d.day} {d.strftime('%b')} {d.year}"


def js_round(x: float) -> int:
    """Math.round from JavaScript (halves round up), so results match the old TypeScript engine."""
    return int(math.floor(x + 0.5))


def round1(x: float) -> float:
    return js_round(x * 10) / 10


_TITLES = {"dr", "prof", "dato", "dato'", "datin", "datuk", "puan", "encik", "en", "cik", "mr", "mrs", "ms", "miss"}


def first_name(name: str) -> str:
    """'Dr. Sara Tan (Demo)' → 'Sara' (skips titles)."""
    words = [w for w in (name or "").split() if w]
    for w in words:
        if w.lower().rstrip(".") not in _TITLES:
            return w.strip("(),")
    return name or ""
