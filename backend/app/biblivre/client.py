"""
bibsimples - Cliente HTTP para o Biblivre
======================================

Este é o módulo central de comunicação com o Biblivre.
Encapsula toda a lógica de requisições HTTP, gerenciamento de sessão,
e parsing de respostas.

Arquitetura:
    BiblioClient é a classe principal que gerencia:
    - Conexão HTTP (via httpx)
    - Sessão/cookies (autenticação)
    - Serialização de requisições
    - Parsing de respostas JSON
    - Tratamento de erros

Design Decisions:
    1. Usa httpx ao invés de requests para suporte assíncrono nativo
    2. AsyncClient com context manager para gerenciar conexões
    3. Métodos separados para cada ação do Biblivre
    4. Exceções específicas para cada tipo de erro

Compatibilidade:
    - Windows, Linux, macOS
    - Python 3.11+
    - Biblivre 5.x

Exemplo de Uso:
    async with BiblioClient(base_url="http://localhost/Biblivre5") as client:
        # Login
        await client.login("admin", "admin")
        
        # Pesquisar
        results = await client.search("Dom Casmurro")
        
        # Buscar registro específico
        record = await client.get_record(id=123)

Notas:
    - O Biblivre usa uma API JSON interna não documentada
    - Os endpoints seguem padrão: ?controller=json&module=X&action=Y
    - A sessão é mantida via cookie JSESSIONID
"""

import json
import logging
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from .exceptions import (
    BiblioAuthError,
    BiblioConnectionError,
    BiblioException,
    BiblioNotFoundError,
    BiblioServerError,
    BiblioSessionExpiredError,
    BiblioValidationError,
)

# Configuração de logging
logger = logging.getLogger(__name__)


class BiblioClient:
    """
    Cliente HTTP assíncrono para comunicação com o Biblivre.
    
    Esta classe encapsula toda a comunicação com a API JSON interna
    do Biblivre, fornecendo uma interface Python limpa e tipada.
    
    Attributes:
        base_url: URL base do Biblivre (ex: http://localhost/Biblivre5)
        schema: Schema do Biblivre (geralmente "default")
        timeout: Timeout em segundos para requisições
        _client: Instância do httpx.AsyncClient (gerenciada internamente)
        _logged_in: Flag indicando se há sessão ativa
    
    Exemplo:
        # Uso recomendado: context manager
        async with BiblioClient() as client:
            await client.login("user", "pass")
            records = await client.search("machado")
        
        # Uso alternativo: manual
        client = BiblioClient()
        await client.connect()
        try:
            await client.login("user", "pass")
        finally:
            await client.disconnect()
    """
    
    # ==========================================================================
    # Constantes
    # ==========================================================================
    
    # Controller padrão para requisições JSON
    DEFAULT_CONTROLLER = "json"
    
    # Módulos do Biblivre
    MODULE_LOGIN = "login"
    MODULE_CATALOGING_BIBLIO = "cataloging.bibliographic"
    MODULE_CATALOGING_HOLDING = "cataloging.holding"
    MODULE_CIRCULATION = "circulation"
    
    # Ações comuns
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_SEARCH = "search"
    ACTION_PAGINATE = "paginate"
    ACTION_OPEN = "open"
    ACTION_SAVE = "save"
    ACTION_DELETE = "delete"
    ACTION_CREATE_AUTOMATIC_HOLDING = "create_automatic_holding"
    
    # ==========================================================================
    # Inicialização
    # ==========================================================================
    
    def __init__(
        self,
        base_url: str = "http://localhost/Biblivre5",
        schema: str = "default",
        timeout: float = 30.0,
    ):
        """
        Inicializa o cliente Biblivre.
        
        Args:
            base_url: URL base do servidor Biblivre (sem barra final)
            schema: Schema/instância do Biblivre (default: "default")
            timeout: Timeout em segundos para requisições (default: 30)
        
        Note:
            O cliente não está conectado após a inicialização.
            Use `connect()` ou o context manager `async with`.
        """
        # Remove barra final se houver
        self.base_url = base_url.rstrip("/")
        self.schema = schema
        self.timeout = timeout
        
        # Estado interno
        self._client: Optional[httpx.AsyncClient] = None
        self._logged_in: bool = False
        self._user_id: Optional[int] = None
        self._user_name: Optional[str] = None
    
    # ==========================================================================
    # Context Manager (async with)
    # ==========================================================================
    
    async def __aenter__(self) -> "BiblioClient":
        """
        Entra no context manager, conectando o cliente.
        
        Permite usar:
            async with BiblioClient() as client:
                ...
        """
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Sai do context manager, desconectando o cliente.
        
        Automaticamente faz logout se estiver logado e
        fecha a conexão HTTP.
        """
        await self.disconnect()
    
    # ==========================================================================
    # Gerenciamento de Conexão
    # ==========================================================================
    
    async def connect(self) -> None:
        """
        Estabelece conexão HTTP com o Biblivre.
        
        Cria um httpx.AsyncClient com configurações apropriadas.
        O cliente mantém cookies automaticamente (para sessão).
        
        Raises:
            BiblioConnectionError: Se não conseguir conectar
        """
        if self._client is not None:
            logger.warning("Cliente já está conectado")
            return
        
        try:
            # Cria cliente HTTP com:
            # - Timeout configurável
            # - Cookies automáticos (para sessão)
            # - Headers padrão
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                headers={
                    "User-Agent": "bibsimples/0.1.0",
                    "Accept": "application/json, text/javascript, */*",
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                },
            )
            logger.info(f"Cliente conectado a {self.base_url}")
            
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            raise BiblioConnectionError(
                f"Não foi possível criar conexão HTTP",
                original_error=e
            )
    
    async def disconnect(self) -> None:
        """
        Encerra conexão HTTP com o Biblivre.
        
        Automaticamente faz logout se estiver logado.
        """
        if self._client is None:
            return
        
        # Tenta fazer logout se estiver logado
        if self._logged_in:
            try:
                await self.logout()
            except BiblioException:
                # Ignora erros no logout ao desconectar
                pass
        
        # Fecha o cliente HTTP
        await self._client.aclose()
        self._client = None
        logger.info("Cliente desconectado")
    
    @property
    def is_connected(self) -> bool:
        """Verifica se o cliente está conectado."""
        return self._client is not None
    
    @property
    def is_logged_in(self) -> bool:
        """Verifica se há sessão ativa."""
        return self._logged_in
    
    # ==========================================================================
    # Métodos Internos de Requisição
    # ==========================================================================
    
    def _build_url(self, module: str, action: str, **params) -> str:
        """
        Constrói URL para requisição ao Biblivre.
        
        O Biblivre usa um padrão de URL com query params:
            /Biblivre5/default?controller=json&module=X&action=Y&param=value
        
        Args:
            module: Módulo do Biblivre (ex: "login", "cataloging.bibliographic")
            action: Ação a executar (ex: "login", "search")
            **params: Parâmetros adicionais
        
        Returns:
            URL completa para a requisição
        """
        # Parâmetros base
        query_params = {
            "controller": self.DEFAULT_CONTROLLER,
            "module": module,
            "action": action,
        }
        
        # Adiciona parâmetros extras
        query_params.update(params)
        
        # Constrói URL (schema opcional — instâncias single-schema não têm path segment)
        if self.schema:
            url = f"{self.base_url}/{self.schema}/?{urlencode(query_params)}"
        else:
            url = f"{self.base_url}/?{urlencode(query_params)}"
        return url
    
    async def _request(
        self,
        method: str,
        module: str,
        action: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Executa requisição HTTP ao Biblivre.
        
        Método interno que:
        1. Constrói a URL
        2. Executa a requisição
        3. Parseia a resposta JSON
        4. Verifica erros
        5. Retorna dados ou levanta exceção
        
        Args:
            method: Método HTTP ("GET" ou "POST")
            module: Módulo do Biblivre
            action: Ação a executar
            data: Dados para POST (form-encoded)
            params: Parâmetros de URL adicionais
        
        Returns:
            Dicionário com resposta do Biblivre
        
        Raises:
            BiblioConnectionError: Erro de rede
            BiblioAuthError: Erro de autenticação
            BiblioServerError: Erro do servidor
            BiblioException: Outros erros
        """
        # Verifica se está conectado
        if self._client is None:
            raise BiblioConnectionError("Cliente não está conectado")
        
        # Constrói URL
        url_params = params or {}
        url = self._build_url(module, action, **url_params)
        
        logger.debug(f"Requisição {method} para {url}")
        
        try:
            # Executa requisição
            if method.upper() == "GET":
                response = await self._client.get(url)
            else:
                response = await self._client.post(url, data=data)
            
            # Log de debug
            logger.debug(f"Status: {response.status_code}")
            
            # Verifica status HTTP
            if response.status_code >= 500:
                raise BiblioServerError(
                    f"Erro interno do servidor (HTTP {response.status_code})"
                )
            
            # Parseia JSON
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Resposta não é JSON válido: {response.text[:200]}")
                raise BiblioServerError(
                    "Resposta do Biblivre não é JSON válido",
                    original_error=e
                )
            
            # Verifica erros na resposta
            self._check_response_errors(result)
            
            return result
            
        except httpx.TimeoutException as e:
            logger.error(f"Timeout na requisição: {e}")
            raise BiblioConnectionError(
                f"Timeout ao conectar ao Biblivre ({self.timeout}s)",
                original_error=e
            )
        except httpx.ConnectError as e:
            logger.error(f"Erro de conexão: {e}")
            raise BiblioConnectionError(
                "Não foi possível conectar ao Biblivre. Verifique se o servidor está online.",
                original_error=e
            )
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP: {e}")
            raise BiblioConnectionError(
                f"Erro HTTP: {e}",
                original_error=e
            )
    
    def _check_response_errors(self, response: dict) -> None:
        """
        Verifica erros na resposta do Biblivre.
        
        O Biblivre retorna erros de várias formas:
        - Campo "success" = false
        - Campo "message" com erro
        - Campo "error" com descrição
        
        Args:
            response: Dicionário com resposta do Biblivre
        
        Raises:
            Exceção apropriada baseada no erro
        """
        # Verifica campo success
        if response.get("success") is False:
            message = response.get("message", "Erro desconhecido")
            
            # Detecta tipo de erro pela mensagem
            message_lower = message.lower()
            
            # Erros de "não encontrado" (verificar antes de auth pois "cataloging" contém "login")
            if ("record_not_found" in message_lower or 
                  "not_found" in message_lower or 
                  "not found" in message_lower or 
                  "não encontrad" in message_lower):
                raise BiblioNotFoundError(message)
            
            # Erros de "sem resultados"
            elif ("no_records" in message_lower or
                  "no records" in message_lower or
                  "sem resultado" in message_lower or
                  "nenhum registro" in message_lower):
                raise BiblioNotFoundError(message)
            
            # Erros de autenticação (usar padrões mais específicos)
            elif (".login" in message_lower or 
                  "login." in message_lower or 
                  message_lower.startswith("login") or
                  "senha" in message_lower or 
                  "password" in message_lower or
                  "credencial" in message_lower):
                raise BiblioAuthError(message)
            
            # Erros de validação
            elif "invalid" in message_lower or "inválid" in message_lower:
                raise BiblioValidationError(message)
            
            # Erros de sessão
            elif "session" in message_lower or "sessão" in message_lower:
                raise BiblioSessionExpiredError(message)
            
            # Outros erros
            else:
                raise BiblioException(message)
    
    # ==========================================================================
    # Autenticação
    # ==========================================================================
    
    async def login(self, username: str, password: str) -> dict[str, Any]:
        """
        Faz login no Biblivre.
        
        Autentica o usuário e estabelece uma sessão. O cookie de sessão
        é mantido automaticamente pelo cliente HTTP.
        
        Args:
            username: Nome de usuário do Biblivre
            password: Senha do usuário
        
        Returns:
            Dicionário com informações do usuário logado:
            {
                "success": true,
                "id": 1,
                "name": "Administrador",
                ...
            }
        
        Raises:
            BiblioAuthError: Credenciais inválidas
            BiblioConnectionError: Erro de conexão
        
        Exemplo:
            user_info = await client.login("admin", "admin")
            print(f"Logado como: {user_info.get('name')}")
        """
        logger.info(f"Tentando login como '{username}'")
        
        # Dados do formulário de login
        form_data = {
            "username": username,
            "password": password,
        }
        
        try:
            result = await self._request(
                method="POST",
                module=self.MODULE_LOGIN,
                action=self.ACTION_LOGIN,
                data=form_data,
            )
            
            # Verifica se login foi bem-sucedido
            # O Biblivre retorna dados do usuário em caso de sucesso
            if result.get("success") is False:
                raise BiblioAuthError(
                    result.get("message", "Usuário ou senha inválidos")
                )
            
            # Atualiza estado interno
            self._logged_in = True
            self._user_id = result.get("id")
            self._user_name = result.get("name")
            
            logger.info(f"Login bem-sucedido: {self._user_name} (ID: {self._user_id})")
            return result
            
        except BiblioAuthError:
            self._logged_in = False
            raise
    
    async def logout(self) -> None:
        """
        Faz logout do Biblivre.
        
        Encerra a sessão atual. Os cookies são mantidos mas a sessão
        no servidor é invalidada.
        
        Raises:
            BiblioConnectionError: Erro de conexão
        """
        if not self._logged_in:
            logger.warning("Tentativa de logout sem estar logado")
            return
        
        logger.info(f"Fazendo logout do usuário {self._user_name}")
        
        try:
            await self._request(
                method="POST",
                module=self.MODULE_LOGIN,
                action=self.ACTION_LOGOUT,
            )
        finally:
            # Limpa estado mesmo se der erro
            self._logged_in = False
            self._user_id = None
            self._user_name = None
        
        logger.info("Logout realizado")
    
    # ==========================================================================
    # Pesquisa
    # ==========================================================================
    
    async def search(
        self,
        query: str,
        database: str = "main",
        material_type: str = "all",
        search_mode: str = "simple",
    ) -> dict[str, Any]:
        """
        Pesquisa registros no Biblivre.
        
        Executa uma busca no acervo da biblioteca. Suporta busca simples
        (termo em qualquer campo) ou avançada (campos específicos).
        
        Args:
            query: Termo de busca
            database: Base de dados ("main", "work", "private", "trash")
            material_type: Tipo de material ("all", "book", "serial", etc.)
            search_mode: Tipo de busca ("simple", "advanced")
        
        Returns:
            Dicionário com resultados:
            {
                "search": {
                    "id": 123,
                    "record_count": 45,
                    "page": 1,
                    "data": [...registros...]
                }
            }
        
        Raises:
            BiblioAuthError: Não está logado
            BiblioConnectionError: Erro de conexão
        
        Exemplo:
            results = await client.search("Dom Casmurro")
            for record in results["search"]["data"]:
                print(record["title"])
        """
        logger.debug(f"Pesquisando: '{query}' em {database}")
        
        # Monta parâmetros de busca (formato JSON)
        search_params = {
            # Compatibilidade: versões do Biblivre usam "search_mode" (oficial)
            # e algumas integrações antigas usam "search_type".
            "search_mode": search_mode,
            "search_type": search_mode,
            "database": database,
            "material_type": material_type,
            "search_terms": [{"query": query}],
        }
        
        result = await self._request(
            method="GET",
            module=self.MODULE_CATALOGING_BIBLIO,
            action=self.ACTION_SEARCH,
            params={"search_parameters": json.dumps(search_params)},
        )
        
        # Log de resultados
        if "search" in result:
            count = result["search"].get("record_count", 0)
            logger.info(f"Busca retornou {count} resultado(s)")
        
        return result
    
    async def paginate(
        self,
        search_id: int,
        page: int = 1,
        indexing_group: int = 0,
    ) -> dict[str, Any]:
        """
        Pagina resultados de uma busca.
        
        Após executar uma busca com `search()`, use este método para
        navegar entre as páginas de resultados.
        
        Args:
            search_id: ID da busca (retornado por search())
            page: Número da página (começa em 1)
            indexing_group: Grupo de indexação para filtro
        
        Returns:
            Dicionário com resultados da página solicitada
        
        Exemplo:
            results = await client.search("machado")
            search_id = results["search"]["id"]
            
            page2 = await client.paginate(search_id, page=2)
        """
        logger.debug(f"Paginando busca {search_id}, página {page}")
        
        return await self._request(
            method="GET",
            module=self.MODULE_CATALOGING_BIBLIO,
            action=self.ACTION_PAGINATE,
            params={
                "search_id": search_id,
                "page": page,
                "indexing_group": indexing_group,
            },
        )
    
    # ==========================================================================
    # Registros Bibliográficos
    # ==========================================================================
    
    async def get_record(self, record_id: int) -> dict[str, Any]:
        """
        Obtém detalhes de um registro bibliográfico.
        
        Retorna informações completas de um registro, incluindo:
        - Dados bibliográficos (MARC)
        - Exemplares (holdings)
        - Informações de empréstimo
        
        Args:
            record_id: ID do registro no Biblivre
        
        Returns:
            Dicionário com dados do registro:
            {
                "data": {
                    "id": 123,
                    "title": "Dom Casmurro",
                    "author": "Machado de Assis",
                    "marc": "...",
                    "json": {...},
                    "holdings": [...],
                    ...
                }
            }
        
        Raises:
            BiblioNotFoundError: Registro não encontrado
        
        Exemplo:
            record = await client.get_record(123)
            print(record["data"]["title"])
        """
        logger.debug(f"Obtendo registro ID {record_id}")
        
        result = await self._request(
            method="GET",
            module=self.MODULE_CATALOGING_BIBLIO,
            action=self.ACTION_OPEN,
            params={"id": record_id},
        )
        
        # Verifica se encontrou
        if "data" not in result or result.get("data") is None:
            raise BiblioNotFoundError(
                f"Registro {record_id} não encontrado",
                resource_type="record",
                resource_id=record_id,
            )
        
        return result
    
    async def save_record(
        self,
        data: dict[str, Any],
        record_id: int = 0,
        data_format: str = "FORM",
        material_type: str = "book",
        database: str = "work",
    ) -> dict[str, Any]:
        """
        Salva (cria ou atualiza) um registro bibliográfico.
        
        Args:
            data: Dados do registro (formato depende de data_format)
            record_id: ID do registro (0 para novo registro)
            data_format: Formato dos dados ("FORM", "MARC")
            material_type: Tipo de material
            database: Base de dados destino
        
        Returns:
            Dicionário com registro salvo, incluindo ID gerado
        
        Raises:
            BiblioValidationError: Dados inválidos
            BiblioAuthError: Sem permissão
        
        Exemplo:
            # Criar novo registro
            new_record = await client.save_record(
                data={"title": "Novo Livro", "author": "Autor"},
                record_id=0
            )
            
            # Atualizar existente
            await client.save_record(
                data=updated_data,
                record_id=123
            )
        """
        logger.info(f"Salvando registro (ID: {record_id or 'novo'})")
        
        form_data = {
            "id": record_id,
            "from": data_format,
            "material_type": material_type,
            "database": database,
            "data": json.dumps(data) if isinstance(data, dict) else data,
        }
        
        result = await self._request(
            method="POST",
            module=self.MODULE_CATALOGING_BIBLIO,
            action=self.ACTION_SAVE,
            data=form_data,
        )
        
        return result
    
    async def delete_record(
        self,
        record_id: int,
        database: str = "work",
    ) -> dict[str, Any]:
        """
        Move um registro para a lixeira ou exclui permanentemente.
        
        Args:
            record_id: ID do registro a excluir
            database: Base onde está o registro
        
        Returns:
            Dicionário confirmando exclusão
        
        Raises:
            BiblioNotFoundError: Registro não encontrado
            BiblioAuthError: Sem permissão
        """
        logger.info(f"Excluindo registro ID {record_id}")
        
        form_data = {
            "id": record_id,
            "database": database,
        }
        
        return await self._request(
            method="POST",
            module=self.MODULE_CATALOGING_BIBLIO,
            action=self.ACTION_DELETE,
            data=form_data,
        )
    
    # ==========================================================================
    # Exemplares (Holdings)
    # ==========================================================================
    
    async def get_holdings(self, record_id: int) -> list[dict[str, Any]]:
        """
        Lista exemplares de um registro bibliográfico.
        
        Args:
            record_id: ID do registro bibliográfico
        
        Returns:
            Lista de exemplares com seus dados
        
        Exemplo:
            holdings = await client.get_holdings(123)
            for h in holdings:
                print(f"Exemplar {h['accession_number']}: {h['availability']}")
        """
        logger.debug(f"Obtendo exemplares do registro {record_id}")
        
        # Os exemplares já vêm com o registro
        record = await self.get_record(record_id)
        
        holdings = record.get("data", {}).get("holdings", [])
        return holdings
    
    async def save_holding(
        self,
        record_id: int,
        holding_data: dict[str, Any],
        holding_id: int = 0,
    ) -> dict[str, Any]:
        """
        Salva (cria ou atualiza) um exemplar.
        
        Args:
            record_id: ID do registro bibliográfico
            holding_data: Dados do exemplar
            holding_id: ID do exemplar (0 para novo)
        
        Returns:
            Dicionário com exemplar salvo
        
        Exemplo:
            # Adicionar novo exemplar
            holding = await client.save_holding(
                record_id=123,
                holding_data={
                    "accession_number": "2024/001",
                    "location": "Estante A"
                }
            )
        """
        logger.info(f"Salvando exemplar para registro {record_id}")
        
        form_data = {
            "id": holding_id,
            "record_id": record_id,
            "from": "HOLDING_FORM",
            "data": json.dumps(holding_data),
        }
        
        return await self._request(
            method="POST",
            module=self.MODULE_CATALOGING_HOLDING,
            action=self.ACTION_SAVE,
            data=form_data,
        )

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
    ) -> dict[str, Any]:
        """
        Cria exemplares automaticamente para um registro bibliográfico.

        Este método usa a mesma ação da interface do Biblivre para criar
        múltiplos exemplares de uma vez.
        """
        logger.info(
            "Criando %s exemplar(es) automático(s) para registro %s",
            holding_count,
            record_id,
        )

        form_data = {
            "record_id": record_id,
            "database": database,
            "holding_count": holding_count,
            "holding_volume_number": holding_volume_number,
            "holding_volume_count": holding_volume_count,
            "holding_library": holding_library,
            "holding_acquisition_type": holding_acquisition_type,
            "holding_acquisition_date": holding_acquisition_date,
        }

        return await self._request(
            method="POST",
            module=self.MODULE_CATALOGING_HOLDING,
            action=self.ACTION_CREATE_AUTOMATIC_HOLDING,
            data=form_data,
        )
