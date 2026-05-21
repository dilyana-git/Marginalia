from fastapi.testclient import TestClient

from app.models import Work


def test_create_and_get_entry(client: TestClient, work: Work) -> None:
    body = {
        "work_id": work.id,
        "date": "2025-01-15",
        "body": "This chapter was fascinating.",
        "kind": "reflection",
    }
    r = client.post("/api/journal", json=body)
    assert r.status_code == 201
    entry = r.json()
    assert entry["body"] == "This chapter was fascinating."
    assert entry["kind"] == "reflection"
    assert entry["work_id"] == work.id

    r2 = client.get(f"/api/journal/{entry['id']}")
    assert r2.status_code == 200


def test_list_journal_filter_work(client: TestClient, work: Work) -> None:
    client.post("/api/journal", json={"work_id": work.id, "date": "2025-01-15", "body": "note"})
    r = client.get(f"/api/journal?work_id={work.id}")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_list_journal_filter_kind(client: TestClient) -> None:
    client.post("/api/journal", json={"date": "2025-01-15", "body": "a quote", "kind": "quote"})
    r = client.get("/api/journal?kind=quote")
    assert r.status_code == 200
    assert all(e["kind"] == "quote" for e in r.json())


def test_update_entry(client: TestClient) -> None:
    created = client.post(
        "/api/journal", json={"date": "2025-01-15", "body": "original", "kind": "free"}
    ).json()
    r = client.put(f"/api/journal/{created['id']}", json={"body": "updated body"})
    assert r.status_code == 200
    assert r.json()["body"] == "updated body"


def test_delete_entry(client: TestClient) -> None:
    created = client.post(
        "/api/journal", json={"date": "2025-01-15", "body": "temporary", "kind": "free"}
    ).json()
    r = client.delete(f"/api/journal/{created['id']}")
    assert r.status_code == 204


def test_freestanding_entry(client: TestClient) -> None:
    body = {"date": "2025-03-01", "body": "No book attached.", "kind": "free"}
    r = client.post("/api/journal", json=body)
    assert r.status_code == 201
    assert r.json()["work_id"] is None
