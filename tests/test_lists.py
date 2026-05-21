from fastapi.testclient import TestClient

from app.models import ReadingList, Work


def test_create_and_get_list(client: TestClient) -> None:
    r = client.post("/api/lists", json={"name": "Favourites"})
    assert r.status_code == 201
    lst = r.json()
    assert lst["name"] == "Favourites"
    assert lst["is_system"] is False

    r2 = client.get(f"/api/lists/{lst['id']}")
    assert r2.status_code == 200
    assert r2.json()["items"] == []


def test_cannot_delete_system_list(client: TestClient, system_list: ReadingList) -> None:
    r = client.delete(f"/api/lists/{system_list.id}")
    assert r.status_code == 409


def test_add_and_remove_item(client: TestClient, work: Work) -> None:
    # Create a list
    lst = client.post("/api/lists", json={"name": "My List"}).json()
    lst_id = lst["id"]

    # Add item
    r = client.post(f"/api/lists/{lst_id}/items", json={"work_id": work.id})
    assert r.status_code == 201
    assert r.json()["work_id"] == work.id

    # Verify in detail
    detail = client.get(f"/api/lists/{lst_id}").json()
    assert len(detail["items"]) == 1

    # Remove
    r2 = client.delete(f"/api/lists/{lst_id}/items/{work.id}")
    assert r2.status_code == 204

    detail2 = client.get(f"/api/lists/{lst_id}").json()
    assert len(detail2["items"]) == 0
