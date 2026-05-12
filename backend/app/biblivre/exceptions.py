"""
bibsimples - Exceções do Módulo Biblivre
=====================================

Define exceções específicas para erros na comunicação com o Biblivre.
Isso permite tratamento de erros mais granular e mensagens claras.

Hierarquia:
    BiblioException (base)
    ├── BiblioConnectionError     - Erros de conexão (rede, timeout)
    ├── BiblioAuthError           - Erros de autenticação
    ├── BiblioNotFoundError       - Recurso não encontrado
    ├── BiblioValidationError     - Dados inválidos
    └── BiblioServerError         - Erros internos do Biblivre
"""

from typing import Any, Optional


class BiblioException(Exception):
    """
    Exceção base para todos os erros relacionados ao Biblivre.
    
    Todas as outras exceções do módulo herdam desta classe,
    permitindo capturar qualquer erro do Biblivre com:
    
        try:
            await client.search(...)
        except BiblioException as e:
            logger.error(f"Erro no Biblivre: {e}")
    
    Attributes:
        message: Mensagem de erro descritiva
        details: Detalhes adicionais (opcional)
        original_error: Exceção original que causou este erro (opcional)
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Representação em string da exceção."""
        if self.details:
            return f"{self.message} - Detalhes: {self.details}"
        return self.message
    
    def to_dict(self) -> dict[str, Any]:
        """Converte a exceção para dicionário (útil para APIs)."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class BiblioConnectionError(BiblioException):
    """
    Erro de conexão com o servidor Biblivre.
    
    Ocorre quando:
    - O servidor não está acessível
    - Timeout na requisição
    - Erro de DNS
    - Erro de SSL/TLS
    
    Exemplo:
        try:
            await client.login(user, password)
        except BiblioConnectionError:
            print("Não foi possível conectar ao Biblivre. Verifique a rede.")
    """
    
    def __init__(
        self,
        message: str = "Não foi possível conectar ao servidor Biblivre",
        **kwargs
    ):
        super().__init__(message, **kwargs)


class BiblioAuthError(BiblioException):
    """
    Erro de autenticação no Biblivre.
    
    Ocorre quando:
    - Credenciais inválidas (usuário/senha)
    - Sessão expirada
    - Usuário sem permissão para a ação
    - Token inválido
    
    Exemplo:
        try:
            await client.login(user, password)
        except BiblioAuthError:
            print("Usuário ou senha incorretos")
    """
    
    def __init__(
        self,
        message: str = "Falha na autenticação com o Biblivre",
        **kwargs
    ):
        super().__init__(message, **kwargs)


class BiblioNotFoundError(BiblioException):
    """
    Recurso não encontrado no Biblivre.
    
    Ocorre quando:
    - Registro bibliográfico não existe
    - Exemplar não encontrado
    - Usuário não cadastrado
    - Pesquisa sem resultados (em alguns contextos)
    
    Exemplo:
        try:
            record = await client.get_record(id=999999)
        except BiblioNotFoundError:
            print("Registro não encontrado")
    """
    
    def __init__(
        self,
        message: str = "Recurso não encontrado no Biblivre",
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        kwargs["details"] = details
        super().__init__(message, **kwargs)


class BiblioValidationError(BiblioException):
    """
    Erro de validação de dados no Biblivre.
    
    Ocorre quando:
    - Dados do registro estão incompletos
    - Formato MARC inválido
    - Campos obrigatórios ausentes
    - Valores fora do range permitido
    
    Exemplo:
        try:
            await client.save_record(invalid_data)
        except BiblioValidationError as e:
            print(f"Dados inválidos: {e.details}")
    """
    
    def __init__(
        self,
        message: str = "Dados inválidos para o Biblivre",
        field: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        kwargs["details"] = details
        super().__init__(message, **kwargs)


class BiblioServerError(BiblioException):
    """
    Erro interno do servidor Biblivre.
    
    Ocorre quando:
    - Erro 500 do servidor
    - Banco de dados indisponível
    - Erro não tratado no Biblivre
    
    Geralmente não há ação que o usuário possa tomar,
    além de tentar novamente mais tarde.
    
    Exemplo:
        try:
            await client.save_record(data)
        except BiblioServerError:
            print("Erro interno no Biblivre. Tente novamente.")
    """
    
    def __init__(
        self,
        message: str = "Erro interno no servidor Biblivre",
        **kwargs
    ):
        super().__init__(message, **kwargs)


class BiblioSessionExpiredError(BiblioAuthError):
    """
    Sessão expirada no Biblivre.
    
    Subclasse de BiblioAuthError específica para quando a sessão
    expira durante o uso. O cliente deve fazer login novamente.
    
    Exemplo:
        try:
            await client.search(query)
        except BiblioSessionExpiredError:
            # Re-autenticar automaticamente
            await client.login(saved_user, saved_password)
            await client.search(query)
    """
    
    def __init__(
        self,
        message: str = "Sessão expirada. Faça login novamente.",
        **kwargs
    ):
        super().__init__(message, **kwargs)
