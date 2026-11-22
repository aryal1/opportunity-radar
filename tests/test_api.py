from fastapi.testclient import TestClient

from opportunity_radar import store
from opportunity_radar.web import app


def test_api_openapi_and_dataset_actions(tmp_path, monkeypatch):
    database = tmp_path / "api.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database}")
    store._engine.cache_clear()
    monkeypatch.setattr("opportunity_radar.web.search_catalogue", lambda query, pages: [])
    client = TestClient(app)

    synced = client.post("/api/sync", json={"query": ""})
    assert synced.status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert "/api/investigate" in client.get("/openapi.json").json()["paths"]
    assert client.post("/api/save", json={"id": "missing", "saved": True}).status_code == 404
    assert client.post("/api/investigate", json={"query": "x"}).status_code == 422
    assert client.get("/").status_code == 200

    store._engine.cache_clear()


def test_api_validation_limits_search_query():
    client = TestClient(app)
    assert client.get("/api/datasets", params={"q": "x" * 161}).status_code == 422
