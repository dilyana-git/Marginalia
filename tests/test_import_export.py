from fastapi.testclient import TestClient


def test_export_returns_json(client: TestClient) -> None:
    r = client.get("/api/import-export/export")
    assert r.status_code == 200
    data = r.json()
    assert "regions" in data
    assert "works" in data
    assert "exported_at" in data


def test_import_merge_loads_seed(client: TestClient) -> None:
    r = client.post("/api/import-export/import", json={"mode": "merge"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "merge"
    assert body["imported"]["regions"] == 7

    # Verify regions appear in API
    r2 = client.get("/api/regions")
    assert r2.status_code == 200
    assert len(r2.json()) == 7


def test_import_invalid_mode(client: TestClient) -> None:
    r = client.post("/api/import-export/import", json={"mode": "invalid"})
    assert r.status_code == 422


def test_import_replace_clears_then_reseeds(client: TestClient) -> None:
    # First seed
    client.post("/api/import-export/import", json={"mode": "merge"})
    # Create a manual work that should disappear after replace
    client.post(
        "/api/works",
        json={"title": "Manual Work", "authors": [], "format": "book", "seed_origin": "manual"},
    )
    # Replace
    r = client.post("/api/import-export/import", json={"mode": "replace"})
    assert r.status_code == 200
    assert r.json()["mode"] == "replace"

    works_after = client.get("/api/works").json()
    # The manual work should be gone; seed works should remain
    manual = [w for w in works_after if w["title"] == "Manual Work"]
    assert len(manual) == 0


def test_export_after_import_contains_seed_data(client: TestClient) -> None:
    client.post("/api/import-export/import", json={"mode": "merge"})
    r = client.get("/api/import-export/export")
    assert r.status_code == 200
    data = r.json()
    assert len(data["regions"]) == 7
    assert len(data["works"]) > 0
