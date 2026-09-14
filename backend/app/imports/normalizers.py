from __future__ import annotations

import re
import unicodedata
from typing import Any

import pycountry


COUNTRY_ALIASES = {
    "usa": "US",
    "u.s.a.": "US",
    "united states of america": "US",
    "uk": "GB",
    "u.k.": "GB",
    "south korea": "KR",
    "russia": "RU",
}


def clean_text(value: Any) -> str | None:
    if value is None:
        return None

    cleaned = str(value).strip()
    if not cleaned or cleaned.lower() in {
        "none",
        "n/a",
        "na",
        "null",
        "unknown",
        "not available",
    }:
        return None
    return cleaned


def country_to_iso2(value: Any) -> str | None:
    country_name = clean_text(value)
    if country_name is None:
        return None

    alias = COUNTRY_ALIASES.get(country_name.lower())
    if alias:
        return alias

    try:
        return pycountry.countries.lookup(country_name).alpha_2
    except LookupError:
        return None


def slugify(value: str, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or fallback.lower()
