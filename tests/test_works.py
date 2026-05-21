from fastapi.testclient import TestClient

from app.models import Region, Work


def test_create_work(client: TestClient, region: Region) -> None:
    body = {
        "title": "Gödel, Escher, Bach",
        "authors": ["Douglas Hofstadter"],
        "format": "book",
        "tier": "ridge",
        "region_id": region.id,
        "seed_origin": "manual",
    }
    r = client.post("/api/works", json=body)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Gödel, Escher, Bach"
    assert data["authors"] == ["Douglas Hofstadter"]
    assert data["tier"] == "ridge"


def test_list_works_filter_region(client: TestClient, work: Work, region: Region) -> None:
    r = client.get(f"/api/works?region_id={region.id}")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == work.id


def test_list_works_filter_status(client: TestClient, work: Work) -> None:
    r = client.get("/api/works?status=want")
    assert r.status_code == 200
    assert any(w["id"] == work.id for w in r.json())


def test_list_works_search(client: TestClient, work: Work) -> None:
    r = client.get("/api/works?q=Test")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_get_work(client: TestClient, work: Work) -> None:
    r = client.get(f"/api/works/{work.id}")
    assert r.status_code == 200
    assert r.json()["id"] == work.id


def test_update_work(client: TestClient, work: Work) -> None:
    r = client.put(f"/api/works/{work.id}", json={"notes": "very interesting"})
    assert r.status_code == 200
    assert r.json()["notes"] == "very interesting"


def test_patch_work_status(client: TestClient, work: Work) -> None:
    r = client.patch(f"/api/works/{work.id}/status", json={"status": "reading"})
    assert r.status_code == 200
    assert r.json()["status"] == "reading"


def test_delete_work(client: TestClient, work: Work) -> None:
    r = client.delete(f"/api/works/{work.id}")
    assert r.status_code == 204

    r2 = client.get(f"/api/works/{work.id}")
    assert r2.status_code == 404


def test_rating_validation(client: TestClient, region: Region) -> None:
    body = {"title": "X", "authors": [], "format": "book", "seed_origin": "manual", "rating": 6}
    r = client.post("/api/works", json=body)
    assert r.status_code == 422
