from app.imports.normalizers import country_to_iso2, slugify


def test_country_to_iso2_known_countries():
    assert country_to_iso2("Nigeria") == "NG"
    assert country_to_iso2("United Kingdom") == "GB"


def test_country_to_iso2_unknown_values():
    assert country_to_iso2("") is None
    assert country_to_iso2("Operational region") is None


def test_slugify_uses_ascii_fallback():
    assert slugify("Café numérique", "fallback") == "cafe-numerique"
    assert slugify("東京", "fallback") == "fallback"
