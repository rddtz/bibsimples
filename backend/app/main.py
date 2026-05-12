"""
bibsimples Backend - Aplicação Principal FastAPI
==============================================

Este é o ponto de entrada da aplicação FastAPI.

A aplicação fornece uma API REST que serve como intermediária
entre o frontend e o servidor Biblivre.

Estrutura:
    /api/v1/          - Rotas da API versão 1
    /api/v1/auth      - Autenticação
    /api/v1/records   - Registros bibliográficos
    /api/v1/search    - Pesquisa
    /api/v1/holdings  - Exemplares
    /api/v1/utils     - Utilitários (Cutter, etc.)
    /docs             - Documentação Swagger (automática)
    /redoc            - Documentação ReDoc (automática)
    /health           - Health check

Execução:
    # Desenvolvimento (com reload automático)
    uvicorn app.main:app --reload --port 8000
    
    # Produção
    uvicorn app.main:app --host 0.0.0.0 --port 8000

    # Via script cross-platform
    python run.py

Variáveis de ambiente:
    BIBSIMPLES_DEBUG=true           - Modo debug
    BIBSIMPLES_BIBLIVRE_URL=http://... - URL do Biblivre
    BIBSIMPLES_SECRET_KEY=...       - Chave secreta
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings


# ==============================================================================
# Configuração de Logging
# ==============================================================================

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# ==============================================================================
# Lifecycle (Startup/Shutdown)
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o ciclo de vida da aplicação.
    
    Executado no startup e shutdown do servidor.
    Use para inicializar recursos (conexões, cache) e liberar no final.
    """
    # STARTUP
    logger.info("=" * 60)
    logger.info(f"bibsimples Backend v{settings.app_version}")
    logger.info(f"Modo: {'DEBUG' if settings.debug else 'PRODUÇÃO'}")
    logger.info(f"Biblivre URL: {settings.biblivre_url}")
    logger.info("=" * 60)
    
    # Inicializa recursos aqui (ex: pool de conexões, cache)
    # ...
    
    yield
    
    # SHUTDOWN
    logger.info("Encerrando aplicação...")
    # Libera recursos aqui
    # ...
    logger.info("Aplicação encerrada.")


# ==============================================================================
# Criação da Aplicação
# ==============================================================================

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="""
    ## bibsimples API
    
    Interface REST para o sistema Biblivre.
    
    ### Funcionalidades
    
    * **Autenticação** - Login/logout no Biblivre
    * **Pesquisa** - Busca no acervo da biblioteca
    * **Registros** - CRUD de registros bibliográficos
    * **Exemplares** - Gerenciamento de exemplares
    * **Utilitários** - Gerador de código Cutter, formatador de nomes
    
    ### Autenticação
    
    A maioria dos endpoints requer autenticação prévia.
    Use `/api/v1/auth/login` para obter uma sessão.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
)


# ==============================================================================
# Middleware
# ==============================================================================

# CORS - Cross-Origin Resource Sharing
# Permite que o frontend (em porta diferente) acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Rotas Básicas
# ==============================================================================


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    response_description="Status de saúde da API",
)
async def health_check():
    """
    Verifica se a API está saudável.
    
    Use para monitoramento e load balancers.
    Retorna:
    - status: "healthy" se tudo estiver ok
    - biblivre: Status da conexão com o Biblivre
    """
    # TODO: Adicionar verificação real de conexão com Biblivre
    return {
        "status": "healthy",
        "biblivre": {
            "url": settings.biblivre_url,
            "status": "configured",  # Será "connected" ou "disconnected" após verificação
        },
    }


# ==============================================================================
# Rotas da API v1
# ==============================================================================

from app.api.v1 import router as api_v1_router

app.include_router(api_v1_router, prefix="/api/v1")

# Serve frontend static files (built with `npm run build` from frontend/)
# Must be mounted AFTER all API routes so /api/... takes priority
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="frontend")


# ==============================================================================
# Tratamento Global de Erros
# ==============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Tratamento global de exceções não capturadas.
    
    Em produção, retorna mensagem genérica.
    Em debug, inclui detalhes do erro.
    """
    logger.exception(f"Erro não tratado: {exc}")
    
    if settings.debug:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "Ocorreu um erro interno. Tente novamente.",
            },
        )


# ==============================================================================
# Tratamento de Erros do Biblivre
# ==============================================================================

from app.biblivre.exceptions import (
    BiblioAuthError,
    BiblioConnectionError,
    BiblioException,
    BiblioNotFoundError,
    BiblioValidationError,
)


@app.exception_handler(BiblioAuthError)
async def biblio_auth_error_handler(request: Request, exc: BiblioAuthError):
    """Trata erros de autenticação do Biblivre."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=exc.to_dict(),
    )


@app.exception_handler(BiblioNotFoundError)
async def biblio_not_found_handler(request: Request, exc: BiblioNotFoundError):
    """Trata erros de recurso não encontrado."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=exc.to_dict(),
    )


@app.exception_handler(BiblioValidationError)
async def biblio_validation_handler(request: Request, exc: BiblioValidationError):
    """Trata erros de validação."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=exc.to_dict(),
    )


@app.exception_handler(BiblioConnectionError)
async def biblio_connection_handler(request: Request, exc: BiblioConnectionError):
    """Trata erros de conexão com o Biblivre."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=exc.to_dict(),
    )


@app.exception_handler(BiblioException)
async def biblio_exception_handler(request: Request, exc: BiblioException):
    """Trata outros erros do Biblivre."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=exc.to_dict(),
    )


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug,
    )
