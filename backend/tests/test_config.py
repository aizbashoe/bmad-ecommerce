"""AC-4: Settings load from env vars via a single typed object; get_settings() is cached."""

from app.core.config import Settings, get_settings


def test_settings_read_from_env(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENDPOINT", "http://dynamodb-local:8000")
    monkeypatch.setenv("FLAT_SHIPPING", "700")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, http://localhost:3000")
    monkeypatch.setenv("PRODUCTS_TABLE", "Products")

    s = Settings()
    assert s.dynamodb_endpoint == "http://dynamodb-local:8000"
    assert s.flat_shipping == 700
    assert s.products_table == "Products"
    assert s.cors_origins_list == ["http://localhost:5173", "http://localhost:3000"]


def test_defaults_when_env_absent(monkeypatch):
    for var in ("DYNAMODB_ENDPOINT", "FLAT_SHIPPING", "CORS_ORIGINS"):
        monkeypatch.delenv(var, raising=False)
    s = Settings()
    # Empty endpoint => AWS default endpoint path (production parity, AD-8)
    assert s.dynamodb_endpoint == ""
    assert s.flat_shipping == 500
    assert s.aws_region == "us-east-1"


def test_get_settings_is_cached():
    assert get_settings() is get_settings()
