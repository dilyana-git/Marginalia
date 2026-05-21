from fastapi.testclient import TestClient

from app.models import Region


def test_list_regions_empty(client: TestClient) -> None:
    r = client.get("/api/regions")
    assert r.status_code == 200
    assert r.json() == []


def test_create_and_get_region(client: TestClient) -> None:
    body = {"ordinal": 1, "name": "AI", "why": "because transformers"}
    r = client.post("/api/regions", json=body)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "AI"
    assert data["ordinal"] == 1

    r2 = client.get(f"/api/regions/{data['id']}")
    assert r2.status_code == 200
    detail = r2.json()
    assert detail["works_count"] == 0
    assert detail["feeds_count"] == 0


def test_update_region(client: TestClient, region: Region) -> None:
    r = client.put(f"/api/regions/{region.id}", json={"qualifier": "updated qualifier"})
    assert r.status_code == 200
    assert r.json()["qualifier"] == "updated qualifier"


def test_delete_region(client: TestClient, region: Region) -> None:
    r = client.delete(f"/api/regions/{region.id}")
    assert r.status_code == 204

    r2 = client.get(f"/api/regions/{region.id}")
    assert r2.status_code == 404


def test_list_regions_returns_all(client: TestClient) -> None:
    client.post("/api/regions", json={"ordinal": 1, "name": "AI", "why": "a"})
    client.post("/api/regions", json={"ordinal": 2, "name": "Math", "why": "b"})
    r = client.get("/api/regions")
    assert len(r.json()) == 2
