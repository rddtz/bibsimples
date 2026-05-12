"""
bibsimples - Testes do Cliente Biblivre
====================================

Testes do módulo app.biblivre.client (BiblioClient).

Estes testes usam respx para mockar as requisições HTTP,
permitindo testar toda a lógica do cliente sem um servidor real.

Executar com:
    pytest tests/test_client.py -v
    pytest tests/test_client.py -v -k "test_login"

Notas:
    - Todos os testes são assíncronos (pytest-asyncio)
    - O mock do servidor é configurado via fixture mock_biblivre
    - Testes de integração real estão marcados com @pytest.mark.integration
"""

import json
import re
from urllib.parse import parse_qs
import pytest
import respx
from httpx import Response

from app.biblivre import (
    BiblioAuthError,
    BiblioClient,
    BiblioConnectionError,
    BiblioNotFoundError,
)


# Padrões de URL para matching
URL_PATTERN_LOGIN = re.compile(r".*action=login.*")
URL_PATTERN_LOGOUT = re.compile(r".*action=logout.*")
URL_PATTERN_SEARCH = re.compile(r".*action=search.*")
URL_PATTERN_OPEN = re.compile(r".*action=open.*")
URL_PATTERN_SAVE = re.compile(r".*action=save.*")
URL_PATTERN_CREATE_AUTOMATIC_HOLDING = re.compile(r".*action=create_automatic_holding.*")


# ==============================================================================
# Testes de Conexão
# ==============================================================================

class TestClientConnection:
    """Testes de conexão e gerenciamento de estado."""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, settings):
        """Testa ciclo de conexão e desconexão."""
        client = BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        )
        
        assert not client.is_connected
        
        await client.connect()
        assert client.is_connected
        
        await client.disconnect()
        assert not client.is_connected
    
    @pytest.mark.asyncio
    async def test_context_manager(self, settings):
        """Testa uso como context manager (async with)."""
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            assert client.is_connected
        
        # Após sair do contexto, deve estar desconectado
        assert not client.is_connected
    
    @pytest.mark.asyncio
    async def test_double_connect_warning(self, settings):
        """Testa que conectar duas vezes não causa erro."""
        client = BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        )
        
        await client.connect()
        # Segunda conexão não deve causar erro, apenas warning
        await client.connect()
        
        assert client.is_connected
        await client.disconnect()


# ==============================================================================
# Testes de Autenticação
# ==============================================================================

class TestClientLogin:
    """Testes de login e logout."""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_login_success(self, settings, sample_login_response):
        """Testa login bem-sucedido."""
        # Mock da resposta de login usando padrão regex
        respx.post(url=URL_PATTERN_LOGIN).mock(
            return_value=Response(200, json=sample_login_response)
        )
        # Mock do logout (chamado automaticamente no disconnect)
        respx.post(url=URL_PATTERN_LOGOUT).mock(
            return_value=Response(200, json={"success": True})
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            result = await client.login("admin", "admin")
            
            assert result["success"] is True
            assert result["id"] == 1
            assert result["name"] == "Administrador"
            assert client.is_logged_in
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_login_invalid_credentials(self, settings, sample_login_error_response):
        """Testa login com credenciais inválidas."""
        # Mock da resposta de erro
        respx.post(url=URL_PATTERN_LOGIN).mock(
            return_value=Response(200, json=sample_login_error_response)
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            with pytest.raises(BiblioAuthError):
                await client.login("wrong", "credentials")
            
            assert not client.is_logged_in
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_logout(self, settings, sample_login_response):
        """Testa logout."""
        # Mock login
        respx.post(url=URL_PATTERN_LOGIN).mock(
            return_value=Response(200, json=sample_login_response)
        )
        # Mock logout
        respx.post(url=URL_PATTERN_LOGOUT).mock(
            return_value=Response(200, json={"success": True})
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            await client.login("admin", "admin")
            assert client.is_logged_in
            
            await client.logout()
            assert not client.is_logged_in


# ==============================================================================
# Testes de Pesquisa
# ==============================================================================

class TestClientSearch:
    """Testes de pesquisa."""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_search_with_results(self, settings, sample_search_response):
        """Testa pesquisa com resultados."""
        route = respx.get(url=URL_PATTERN_SEARCH).mock(
            return_value=Response(200, json=sample_search_response)
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            result = await client.search("machado")
            
            assert "search" in result
            assert result["search"]["record_count"] == 2
            assert len(result["search"]["data"]) == 2

            assert route.called
            request = route.calls[0].request
            search_parameters = json.loads(request.url.params["search_parameters"])
            assert search_parameters["search_mode"] == "simple"
            assert search_parameters["search_type"] == "simple"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_search_empty(self, settings, sample_empty_search_response):
        """Testa pesquisa sem resultados."""
        respx.get(url=URL_PATTERN_SEARCH).mock(
            return_value=Response(200, json=sample_empty_search_response)
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            # Pesquisa sem resultados levanta BiblioNotFoundError
            with pytest.raises(BiblioNotFoundError):
                await client.search("xyznonexistent")
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_search_with_filters(self, settings, sample_search_response):
        """Testa pesquisa com filtros."""
        respx.get(url=URL_PATTERN_SEARCH).mock(
            return_value=Response(200, json=sample_search_response)
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            result = await client.search(
                query="machado",
                database="main",
                material_type="book",
            )
            
            assert "search" in result


# ==============================================================================
# Testes de Registros
# ==============================================================================

class TestClientRecords:
    """Testes de operações com registros."""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_record(self, settings, sample_record_response):
        """Testa obtenção de registro por ID."""
        respx.get(url=URL_PATTERN_OPEN).mock(
            return_value=Response(200, json=sample_record_response)
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            result = await client.get_record(1)
            
            assert "data" in result
            assert result["data"]["id"] == 1
            assert len(result["data"]["holdings"]) == 2
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_record_not_found(self, settings):
        """Testa obtenção de registro inexistente."""
        respx.get(url=URL_PATTERN_OPEN).mock(
            return_value=Response(200, json={
                "success": False,
                "message": "cataloging.error.record_not_found"
            })
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            with pytest.raises(BiblioNotFoundError):
                await client.get_record(99999)
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_save_new_record(self, settings):
        """Testa criação de novo registro."""
        respx.post(url=URL_PATTERN_SAVE).mock(
            return_value=Response(200, json={
                "success": True,
                "data": {
                    "id": 100,
                    "database": "work",
                }
            })
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            result = await client.save_record(
                data={"title": "Novo Livro", "author": "Autor Teste"},
                record_id=0,  # Novo registro
            )
            
            assert result["success"] is True
            assert result["data"]["id"] == 100


# ==============================================================================
# Testes de Exemplares (Holdings)
# ==============================================================================

class TestClientHoldings:
    """Testes de operações com exemplares."""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_holdings(self, settings, sample_record_response):
        """Testa listagem de exemplares."""
        respx.get(url=URL_PATTERN_OPEN).mock(
            return_value=Response(200, json=sample_record_response)
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            holdings = await client.get_holdings(1)
            
            assert len(holdings) == 2
            assert holdings[0]["accession_number"] == "2024/0001"

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_automatic_holding(self, settings):
        """Testa criação automática de exemplares."""
        route = respx.post(url=URL_PATTERN_CREATE_AUTOMATIC_HOLDING).mock(
            return_value=Response(200, json={"success": True, "list": {"count": 3}})
        )

        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            result = await client.create_automatic_holding(
                record_id=123,
                database="main",
                holding_count=3,
            )

            assert result["success"] is True
            assert route.called
            request = route.calls[0].request
            payload = parse_qs(request.content.decode(), keep_blank_values=True)
            assert payload["record_id"] == ["123"]
            assert payload["database"] == ["main"]
            assert payload["holding_count"] == ["3"]


# ==============================================================================
# Testes de Erros de Conexão
# ==============================================================================

class TestClientConnectionErrors:
    """Testes de tratamento de erros de conexão."""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_connection_timeout(self, settings):
        """Testa timeout de conexão."""
        import httpx
        
        respx.get(url=URL_PATTERN_SEARCH).mock(
            side_effect=httpx.TimeoutException("Connection timed out")
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
            timeout=1.0,
        ) as client:
            with pytest.raises(BiblioConnectionError):
                await client.search("test")
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_server_error(self, settings):
        """Testa erro 500 do servidor."""
        respx.get(url=URL_PATTERN_SEARCH).mock(
            return_value=Response(500, text="Internal Server Error")
        )
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            from app.biblivre import BiblioServerError
            
            with pytest.raises(BiblioServerError):
                await client.search("test")
    
    @pytest.mark.asyncio
    async def test_request_without_connection(self, settings):
        """Testa requisição sem conexão prévia."""
        client = BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        )
        
        # Sem chamar connect()
        with pytest.raises(BiblioConnectionError):
            await client.search("test")


# ==============================================================================
# Testes de Construção de URL
# ==============================================================================

class TestClientUrlBuilding:
    """Testes de construção de URLs."""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_url_format(self, settings):
        """Testa que a URL é construída corretamente."""
        captured_request = None
        
        def capture_request(request):
            nonlocal captured_request
            captured_request = request
            return Response(200, json={"success": True})
        
        respx.get(url=URL_PATTERN_SEARCH).mock(side_effect=capture_request)
        
        async with BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
        ) as client:
            await client.search("test")
        
        # Verifica a URL
        assert captured_request is not None
        url = str(captured_request.url)
        
        assert "controller=json" in url
        assert "module=cataloging.bibliographic" in url
        assert "action=search" in url
    
    def test_base_url_trailing_slash(self):
        """Testa que barra final na URL base é removida."""
        client = BiblioClient(
            base_url="http://localhost/Biblivre5/",
            schema="default",
        )
        
        assert not client.base_url.endswith("/")
        assert client.base_url == "http://localhost/Biblivre5"
