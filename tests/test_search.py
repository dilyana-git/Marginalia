from fastapi.testclient import TestClient

from app.models import Work


def test_search_finds_work(client: TestClient, work: Work) -> None:
    r = client.get("/api/search?q=Test")
    assert r.status_code == 200
    data = r.json()
    assert data["query"] == "Test"
    assert any(w["id"] == work.id for w in data["works"])


def test_search_empty_results(client: TestClient) -> None:
    r = client.get("/api/search?q=xyzzy_nothing_matches")
    assert r.status_code == 200
    data = r.json()
    assert data["works"] == []
    assert data["journal_entries"] == []
    assert data["newsletter_items"] == []


def test_search_requires_q(client: TestClient) -> None:
    r = client.get("/api/search")
    assert r.status_code == 422
