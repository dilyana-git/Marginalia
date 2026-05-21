from fastapi.testclient import TestClient

from app.models import Feed, Region


def test_create_feed(client: TestClient, region: Region) -> None:
    body = {
        "name": "Quanta",
        "type": "rss",
        "kind": "magazine",
        "url": "https://www.quantamagazine.org/feed/",
        "region_id": region.id,
        "seed_origin": "dispatch",
    }
    r = client.post("/api/feeds", json=body)
    assert r.status_code == 201
    assert r.json()["name"] == "Quanta"


def test_list_feeds_filter_region(client: TestClient, feed: Feed, region: Region) -> None:
    r = client.get(f"/api/feeds?region_id={region.id}")
    assert r.status_code == 200
    assert any(f["id"] == feed.id for f in r.json())


def test_list_feeds_filter_active(client: TestClient, feed: Feed) -> None:
    r = client.get("/api/feeds?active=true")
    assert r.status_code == 200
    assert all(f["active"] for f in r.json())


def test_update_feed(client: TestClient, feed: Feed) -> None:
    r = client.put(f"/api/feeds/{feed.id}", json={"active": False})
    assert r.status_code == 200
    assert r.json()["active"] is False


def test_delete_feed(client: TestClient, feed: Feed) -> None:
    r = client.delete(f"/api/feeds/{feed.id}")
    assert r.status_code == 204

    r2 = client.get(f"/api/feeds/{feed.id}")
    assert r2.status_code == 404
