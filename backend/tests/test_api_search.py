import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth import get_biblivre_client
from app.biblivre import BiblioNotFoundError
from app.main import app


@pytest.fixture
def api_client():
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_search_endpoint_returns_normalized_records(api_client, sample_search_response):
    class FakeClient:
        is_logged_in = True
        base_url = "http://test-biblivre.local/Biblivre5"
        schema = "default"

        async def search(self, query: str, database: str = "main", material_type: str = "all"):
            return sample_search_response

    async def override_client():
        return FakeClient()

    app.dependency_overrides[get_biblivre_client] = override_client

    response = api_client.get("/api/v1/search", params={"query": "machado"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["search"]["record_count"] == 2
    assert payload["search"]["data"][0]["title"] == "Dom Casmurro"
    assert payload["search"]["data"][0]["author"] == "Machado de Assis"
    assert payload["search"]["data"][0]["holdings_count"] == 0
    assert "action=open" in payload["search"]["data"][0]["details_url"]


def test_search_endpoint_returns_empty_payload_on_not_found(api_client):
    class FakeClient:
        is_logged_in = True

        async def search(self, query: str, database: str = "main", material_type: str = "all"):
            raise BiblioNotFoundError("cataloging.error.no_records_found")

    async def override_client():
        return FakeClient()

    app.dependency_overrides[get_biblivre_client] = override_client

    response = api_client.get("/api/v1/search", params={"query": "naoexiste"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["search"]["record_count"] == 0
    assert payload["search"]["data"] == []


def test_search_endpoint_requires_login(api_client):
    class FakeClient:
        is_logged_in = False

    async def override_client():
        return FakeClient()

    app.dependency_overrides[get_biblivre_client] = override_client

    response = api_client.get("/api/v1/search", params={"query": "machado"})

    assert response.status_code == 401


def test_search_endpoint_handles_null_and_mixed_types(api_client):
    class FakeClient:
        is_logged_in = True
        base_url = "http://test-biblivre.local/Biblivre4"
        schema = "default"

        async def search(self, query: str, database: str = "main", material_type: str = "all"):
            return {
                "success": True,
                "search": {
                    "id": "10",
                    "record_count": "1",
                    "page": "1",
                    "pages": "1",
                    "data": [
                        {
                            "id": "123",
                            "database": None,
                            "title": None,
                            "author": None,
                            "year": None,
                            "holdings_count": "7",
                            "holdings_available": "5",
                            "holdings_lent": "2",
                            "fields": [
                                {"field": "title", "value": "Livro Teste"},
                                {"field": "author", "value": 999},
                                {"field": "year", "value": 2024},
                            ],
                        }
                    ],
                },
            }

    async def override_client():
        return FakeClient()

    app.dependency_overrides[get_biblivre_client] = override_client

    response = api_client.get("/api/v1/search", params={"query": "teste"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["search"]["id"] == 10
    assert payload["search"]["record_count"] == 1
    assert payload["search"]["data"][0]["id"] == 123
    assert payload["search"]["data"][0]["database"] == "main"
    assert payload["search"]["data"][0]["title"] == "Livro Teste"
    assert payload["search"]["data"][0]["author"] == "999"
    assert payload["search"]["data"][0]["year"] == "2024"
    assert payload["search"]["data"][0]["holdings_count"] == 7
    assert payload["search"]["data"][0]["holdings_available"] == 5
    assert payload["search"]["data"][0]["holdings_lent"] == 2


def test_search_endpoint_handles_unexpected_search_payload(api_client):
    class FakeClient:
        is_logged_in = True

        async def search(self, query: str, database: str = "main", material_type: str = "all"):
            return {"success": True, "search": None}

    async def override_client():
        return FakeClient()

    app.dependency_overrides[get_biblivre_client] = override_client

    response = api_client.get("/api/v1/search", params={"query": "teste"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["search"]["record_count"] == 0
    assert payload["search"]["data"] == []
