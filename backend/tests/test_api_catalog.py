from fastapi.testclient import TestClient
import pytest

from app.api.v1.auth import get_biblivre_client
from app.main import app


@pytest.fixture
def api_client():
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_catalog_create_book_success(api_client):
    captures: dict[str, object] = {}

    class FakeClient:
        is_logged_in = True
        base_url = "http://test-biblivre.local/Biblivre5"
        schema = "default"

        async def save_record(
            self,
            data,
            record_id: int = 0,
            data_format: str = "FORM",
            material_type: str = "book",
            database: str = "work",
        ):
            captures["save_record"] = {
                "data": data,
                "record_id": record_id,
                "data_format": data_format,
                "material_type": material_type,
                "database": database,
            }
            return {"success": True, "data": {"id": 321, "database": "main"}}

        async def create_automatic_holding(
            self,
            record_id: int,
            database: str = "main",
            holding_count: int = 1,
            holding_volume_number: int = 0,
            holding_volume_count: int = 1,
            holding_library: str = "",
            holding_acquisition_type: str = "",
            holding_acquisition_date: str = "",
        ):
            captures["create_automatic_holding"] = {
                "record_id": record_id,
                "database": database,
                "holding_count": holding_count,
                "holding_volume_number": holding_volume_number,
                "holding_volume_count": holding_volume_count,
                "holding_library": holding_library,
                "holding_acquisition_type": holding_acquisition_type,
                "holding_acquisition_date": holding_acquisition_date,
            }
            return {"success": True}

    async def override_client():
        return FakeClient()

    app.dependency_overrides[get_biblivre_client] = override_client

    response = api_client.post(
        "/api/v1/catalog/books",
        json={
            "author_name": "Machado de Assis",
            "title": "Dom Casmurro",
            "cdd": "869.93",
            "cutter_code": "M149",
            "copies": 3,
            "volume": "v.1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["record_id"] == 321
    assert payload["holdings_requested"] == 3
    assert payload["cutter_code"] == "M149"
    assert "action=open" in payload["details_url"]

    saved = captures["save_record"]
    assert saved["record_id"] == 0
    assert saved["data_format"] == "FORM"
    assert saved["material_type"] == "book"
    assert saved["database"] == "main"
    assert saved["data"]["100"][0]["a"] == ["Machado de Assis"]
    assert saved["data"]["245"][0]["a"] == ["Dom Casmurro"]
    assert saved["data"]["082"][0]["a"] == ["869.93"]
    assert saved["data"]["090"][0]["b"] == ["M149"]
    assert saved["data"]["090"][0]["c"] == ["v.1"]

    holdings = captures["create_automatic_holding"]
    assert holdings["record_id"] == 321
    assert holdings["database"] == "main"
    assert holdings["holding_count"] == 3


def test_catalog_create_book_generates_cutter_when_missing(api_client):
    captures: dict[str, object] = {}

    class FakeClient:
        is_logged_in = True
        base_url = "http://test-biblivre.local/Biblivre5"
        schema = "default"

        async def save_record(
            self,
            data,
            record_id: int = 0,
            data_format: str = "FORM",
            material_type: str = "book",
            database: str = "work",
        ):
            captures["data"] = data
            return {"success": True, "data": {"id": 55, "database": "main"}}

        async def create_automatic_holding(self, **kwargs):
            return {"success": True}

    async def override_client():
        return FakeClient()

    app.dependency_overrides[get_biblivre_client] = override_client

    response = api_client.post(
        "/api/v1/catalog/books",
        json={
            "author_name": "José de Alencar",
            "title": "Iracema",
            "cdd": "869.93",
            "copies": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["cutter_code"]
    assert captures["data"]["090"][0]["b"] == [payload["cutter_code"]]


def test_catalog_create_book_requires_login(api_client):
    class FakeClient:
        is_logged_in = False

    async def override_client():
        return FakeClient()

    app.dependency_overrides[get_biblivre_client] = override_client

    response = api_client.post(
        "/api/v1/catalog/books",
        json={
            "author_name": "Autor Teste",
            "title": "Livro Teste",
            "cdd": "000",
            "copies": 1,
        },
    )

    assert response.status_code == 401
