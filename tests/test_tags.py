from fastapi.testclient import TestClient


def test_create_tag_lowercases(client: TestClient) -> None:
    r = client.post("/api/tags", json={"name": "Philosophy"})
    assert r.status_code == 201
    assert r.json()["name"] == "philosophy"


def test_list_tags(client: TestClient) -> None:
    client.post("/api/tags", json={"name": "ai"})
    client.post("/api/tags", json={"name": "math"})
    r = client.get("/api/tags")
    assert r.status_code == 200
    names = [t["name"] for t in r.json()]
    assert "ai" in names
    assert "math" in names


def test_update_tag(client: TestClient) -> None:
    created = client.post("/api/tags", json={"name": "risk"}).json()
    r = client.put(f"/api/tags/{created['id']}", json={"color": "#FF5500"})
    assert r.status_code == 200
    assert r.json()["color"] == "#FF5500"


def test_delete_tag(client: TestClient) -> None:
    created = client.post("/api/tags", json={"name": "temp"}).json()
    r = client.delete(f"/api/tags/{created['id']}")
    assert r.status_code == 204

    r2 = client.get("/api/tags")
    assert not any(t["id"] == created["id"] for t in r2.json())
