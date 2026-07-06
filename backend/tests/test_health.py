"""AC-3: /health returns 200 {"status":"ok"} and OpenAPI is served."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_openapi_served():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["info"]["title"] == "Anonymous E-Commerce Storefront API"
    assert "/health" in body["paths"]


def test_unknown_route_uses_error_envelope():
    """AD-5: 404 (a built-in HTTPException) returns the {error:{code,message}} envelope."""
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert resp.json() == {"error": {"code": "not_found", "message": "Not Found"}}


def test_health_deep_unreachable_returns_503(monkeypatch):
    """When DynamoDB is unreachable, /health/deep returns 503 with the error envelope."""
    import app.api.health as health_mod

    def _boom():
        raise RuntimeError("no dynamodb")

    monkeypatch.setattr(health_mod, "list_table_names", _boom)
    resp = client.get("/health/deep")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "dynamodb_unreachable"


def test_health_deep_ok(monkeypatch):
    """When DynamoDB is reachable, /health/deep reports tables."""
    import app.api.health as health_mod

    monkeypatch.setattr(health_mod, "list_table_names", lambda: ["Products", "Carts"])
    resp = client.get("/health/deep")
    assert resp.status_code == 200
    body = resp.json()
    # Reports reachability + count; does NOT leak the table inventory.
    assert body == {"status": "ok", "dynamodb": "reachable", "tableCount": 2}
    assert "tables" not in body
