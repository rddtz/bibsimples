"""
bibsimples - Configuração de Testes (pytest)
=========================================

Este arquivo configura fixtures e utilidades comuns para todos os testes.

Fixtures disponíveis:
    - client: Cliente BiblioClient mockado
    - mock_biblivre: Mock do servidor Biblivre (via respx)
    - settings: Configurações de teste

Uso:
    def test_something(client, mock_biblivre):
        mock_biblivre.get("/Biblivre5/default?...").respond(json={...})
        result = await client.search("test")
        assert result is not None
"""

import pytest
import respx
from httpx import Response

from app.biblivre import BiblioClient
from app.config import Settings


# ==============================================================================
# Fixtures de Configuração
# ==============================================================================

@pytest.fixture
def settings() -> Settings:
    """
    Configurações de teste.
    
    Retorna uma instância de Settings com valores padrão
    apropriados para testes (não carrega .env).
    """
    return Settings(
        debug=True,
        biblivre_url="http://test-biblivre.local/Biblivre5",
        biblivre_schema="test",
        biblivre_timeout=5.0,
    )


# ==============================================================================
# Fixtures do Cliente Biblivre
# ==============================================================================

@pytest.fixture
async def client(settings: Settings):
    """
    Cliente BiblioClient configurado para testes.
    
    O cliente é conectado no início e desconectado no final do teste.
    Use junto com mock_biblivre para simular respostas.
    
    Exemplo:
        async def test_search(client, mock_biblivre):
            mock_biblivre.get(...).respond(...)
            result = await client.search("test")
    """
    biblio_client = BiblioClient(
        base_url=settings.biblivre_url,
        schema=settings.biblivre_schema,
        timeout=settings.biblivre_timeout,
    )
    
    # Conecta o cliente
    await biblio_client.connect()
    
    yield biblio_client
    
    # Desconecta após o teste
    await biblio_client.disconnect()


@pytest.fixture
def mock_biblivre():
    """
    Mock do servidor Biblivre usando respx.
    
    Permite simular respostas do servidor sem conexão real.
    
    Exemplo:
        def test_login(mock_biblivre, client):
            mock_biblivre.post(
                url__contains="action=login"
            ).respond(json={"success": True, "id": 1, "name": "Admin"})
            
            result = await client.login("admin", "admin")
            assert result["success"] is True
    """
    with respx.mock(assert_all_called=False) as mock:
        yield mock


# ==============================================================================
# Fixtures de Dados de Exemplo
# ==============================================================================

@pytest.fixture
def sample_login_response() -> dict:
    """Resposta de login bem-sucedido."""
    return {
        "success": True,
        "id": 1,
        "name": "Administrador",
        "login": "admin",
        "type": "employee",
    }


@pytest.fixture
def sample_login_error_response() -> dict:
    """Resposta de login com erro."""
    return {
        "success": False,
        "message": "login.error.invalid_credentials",
    }


@pytest.fixture
def sample_search_response() -> dict:
    """Resposta de pesquisa com resultados."""
    return {
        "success": True,
        "search": {
            "id": 123,
            "record_count": 2,
            "page": 1,
            "pages": 1,
            "data": [
                {
                    "id": 1,
                    "database": "main",
                    "fields": [
                        {"field": "title", "value": "Dom Casmurro"},
                        {"field": "author", "value": "Machado de Assis"},
                    ],
                },
                {
                    "id": 2,
                    "database": "main",
                    "fields": [
                        {"field": "title", "value": "Memórias Póstumas de Brás Cubas"},
                        {"field": "author", "value": "Machado de Assis"},
                    ],
                },
            ],
        },
    }


@pytest.fixture
def sample_empty_search_response() -> dict:
    """Resposta de pesquisa sem resultados."""
    return {
        "success": False,
        "message": "cataloging.error.no_records_found",
    }


@pytest.fixture
def sample_record_response() -> dict:
    """Resposta com dados de um registro."""
    return {
        "success": True,
        "data": {
            "id": 1,
            "database": "main",
            "material_type": "book",
            "created": "2024-01-01T10:00:00",
            "modified": "2024-01-15T15:30:00",
            "fields": [
                {"field": "title", "value": "Dom Casmurro"},
                {"field": "author", "value": "Machado de Assis"},
                {"field": "publisher", "value": "Editora XYZ"},
                {"field": "year", "value": "1899"},
            ],
            "marc": "00000nam a2200000 i 4500...",
            "json": {
                "000": "00000nam a2200000 i 4500",
                "100": {"a": "Machado de Assis"},
                "245": {"a": "Dom Casmurro"},
            },
            "holdings": [
                {
                    "id": 10,
                    "accession_number": "2024/0001",
                    "availability": "available",
                },
                {
                    "id": 11,
                    "accession_number": "2024/0002",
                    "availability": "lent",
                },
            ],
        },
    }


# ==============================================================================
# Configuração do pytest-asyncio
# ==============================================================================

# Define o mode padrão como "auto" para detectar automaticamente
# testes assíncronos
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Configuração global do pytest."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
