"""
bibsimples API v1 - Router Principal
=================================

Agrupa todas as rotas da API versão 1.

Estrutura:
    /auth     - Autenticação (login/logout)
    /records  - Registros bibliográficos
    /search   - Pesquisa
    /holdings - Exemplares
    /utils    - Utilitários (Cutter, etc.)
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .catalog import router as catalog_router
from .search import router as search_router
from .utils import router as utils_router

# Router principal da API v1
router = APIRouter(tags=["v1"])

# Inclui sub-routers
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(search_router, prefix="/search", tags=["Search"])
router.include_router(catalog_router, prefix="/catalog", tags=["Catalog"])
router.include_router(utils_router, prefix="/utils", tags=["Utils"])

# TODO: Adicionar quando implementados
# router.include_router(records_router, prefix="/records", tags=["Records"])
# router.include_router(holdings_router, prefix="/holdings", tags=["Holdings"])
