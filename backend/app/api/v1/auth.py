"""
bibsimples API v1 - Rotas de Autenticação
======================================

Endpoints para autenticação no Biblivre.

Endpoints:
    POST /auth/login  - Faz login no Biblivre
    POST /auth/logout - Faz logout do Biblivre
    GET  /auth/me     - Retorna informações do usuário logado

Fluxo de autenticação:
    1. Cliente chama POST /auth/login com credenciais
    2. Backend autentica no Biblivre e retorna token/sessão
    3. Cliente inclui token nas requisições subsequentes
    4. Backend valida token e encaminha para Biblivre

Nota sobre segurança:
    - Senhas nunca são armazenadas no backend
    - A sessão do Biblivre é mantida via cookies
    - O token do bibsimples é usado para identificar a sessão
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.biblivre import BiblioAuthError, BiblioClient
from app.config import settings

router = APIRouter()


# ==============================================================================
# Schemas
# ==============================================================================

class LoginRequest(BaseModel):
    """Dados para login."""
    
    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nome de usuário do Biblivre",
        json_schema_extra={"example": "admin"}
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Senha do usuário",
        json_schema_extra={"example": "admin"}
    )
class LoginResponse(BaseModel):
    """Resposta de login bem-sucedido."""
    
    success: bool = Field(
        default=True,
        description="Indica se o login foi bem-sucedido"
    )
    user_id: int = Field(
        ...,
        description="ID do usuário no Biblivre",
        json_schema_extra={"example": 1}
    )
    name: str = Field(
        ...,
        description="Nome do usuário",
        json_schema_extra={"example": "Administrador"}
    )
    login: str = Field(
        ...,
        description="Login do usuário",
        json_schema_extra={"example": "admin"}
    )
    message: str = Field(
        default="Login realizado com sucesso",
        description="Mensagem descritiva"
    )


class ErrorResponse(BaseModel):
    """Resposta de erro."""
    
    success: bool = Field(
        default=False,
        description="Indica falha"
    )
    error: str = Field(
        ...,
        description="Tipo do erro"
    )
    message: str = Field(
        ...,
        description="Mensagem de erro"
    )


class UserInfo(BaseModel):
    """Informações do usuário logado."""
    
    user_id: int = Field(
        ...,
        description="ID do usuário"
    )
    name: str = Field(
        ...,
        description="Nome do usuário"
    )
    login: str = Field(
        ...,
        description="Login do usuário"
    )
    logged_in: bool = Field(
        default=True,
        description="Indica se está logado"
    )


# ==============================================================================
# Dependências
# ==============================================================================

# Cliente Biblivre compartilhado (em produção, usar pool ou sessões)
_client: Optional[BiblioClient] = None


async def _ensure_biblivre_client() -> BiblioClient:
    """Retorna cliente conectado configurado via settings."""
    global _client

    if _client is None:
        _client = BiblioClient(
            base_url=settings.biblivre_url,
            schema=settings.biblivre_schema,
            timeout=settings.biblivre_timeout,
        )
        await _client.connect()

    return _client


async def get_biblivre_client() -> BiblioClient:
    """
    Obtém instância do cliente Biblivre.
    
    Esta é uma implementação simplificada. Em produção, considere:
    - Pool de conexões
    - Gerenciamento de sessões por usuário
    - Cache de autenticação
    """
    return await _ensure_biblivre_client()


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Credenciais inválidas"},
        503: {"model": ErrorResponse, "description": "Biblivre indisponível"},
    },
    summary="Fazer login",
    description="""
    Autentica o usuário no Biblivre.
    
    Use as mesmas credenciais do acesso direto ao Biblivre.
    
    **Atenção:** A senha é enviada ao servidor apenas para autenticação
    e não é armazenada.
    """,
)
async def login(
    credentials: LoginRequest,
):
    """
    Faz login no Biblivre.
    
    Retorna informações do usuário em caso de sucesso.
    """
    client = await _ensure_biblivre_client()

    try:
        result = await client.login(
            username=credentials.username,
            password=credentials.password,
        )

        user_id = result.get("id") or result.get("user_id") or 0
        user_name = result.get("name") or result.get("fullname") or credentials.username
        user_login = result.get("login") or credentials.username
        
        return LoginResponse(
            success=True,
            user_id=user_id,
            name=user_name,
            login=user_login,
            message="Login realizado com sucesso",
        )
        
    except BiblioAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "AuthenticationError",
                "message": str(e),
            },
        )


@router.post(
    "/logout",
    response_model=dict,
    summary="Fazer logout",
    description="Encerra a sessão atual no Biblivre.",
)
async def logout(
    client: BiblioClient = Depends(get_biblivre_client),
):
    """
    Faz logout do Biblivre.
    
    Encerra a sessão e invalida tokens.
    """
    try:
        await client.logout()
        return {
            "success": True,
            "message": "Logout realizado com sucesso",
        }
    except Exception:
        # Mesmo se der erro, considera logout feito
        return {
            "success": True,
            "message": "Sessão encerrada",
        }


@router.get(
    "/me",
    response_model=UserInfo,
    responses={
        401: {"model": ErrorResponse, "description": "Não autenticado"},
    },
    summary="Informações do usuário",
    description="Retorna informações do usuário atualmente logado.",
)
async def get_current_user(
    client: BiblioClient = Depends(get_biblivre_client),
):
    """
    Retorna informações do usuário logado.
    
    Útil para verificar se a sessão ainda é válida.
    """
    if not client.is_logged_in:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "NotAuthenticated",
                "message": "Usuário não está logado",
            },
        )
    
    return UserInfo(
        user_id=client._user_id or 0,
        name=client._user_name or "",
        login="",  # Não temos essa info facilmente
        logged_in=True,
    )
