"""
bibsimples API - Pacote de Rotas
=============================

Contém todos os routers organizados por versão.
"""

from .v1 import router as v1_router

__all__ = ["v1_router"]
