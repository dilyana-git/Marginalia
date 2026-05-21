from fastapi.testclient import TestClient


def test_get_settings_creates_default(client: TestClient) -> None:
    r = client.get("/api/settings")
    assert r.status_code == 200
    s = r.json()
    assert s["id"] == 1
    assert s["newsletter_enabled"] is True


def test_update_settings(client: TestClient, settings_obj) -> None:
    r = client.put("/api/settings", json={"reader_name": "Dilyana", "max_per_source": 10})
    assert r.status_code == 200
    assert r.json()["reader_name"] == "Dilyana"
    assert r.json()["max_per_source"] == 10
