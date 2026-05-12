"""
bibsimples - Pacote Biblivre
=========================

Este pacote contém toda a lógica de comunicação com o servidor Biblivre.

Módulos:
    - client: Cliente HTTP principal (BiblioClient)
    - exceptions: Exceções específicas
    - auth: Funções auxiliares de autenticação
    - cataloging: Operações de catalogação
    - holdings: Operações com exemplares
    - search: Operações de pesquisa

Uso Básico:
    from app.biblivre import BiblioClient
    
    async with BiblioClient(base_url="http://localhost/Biblivre5") as client:
        await client.login("admin", "admin")
        results = await client.search("machado")

Exceções:
    from app.biblivre.exceptions import BiblioAuthError, BiblioNotFoundError
    
    try:
        await client.login(user, password)
    except BiblioAuthError:
        print("Credenciais inválidas")
"""

from .client import BiblioClient
from .exceptions import (
    BiblioAuthError,
    BiblioConnectionError,
    BiblioException,
    BiblioNotFoundError,
    BiblioServerError,
    BiblioSessionExpiredError,
    BiblioValidationError,
)

# Exporta as classes principais
__all__ = [
    # Cliente principal
    "BiblioClient",
    
    # Exceções
    "BiblioException",
    "BiblioConnectionError",
    "BiblioAuthError",
    "BiblioNotFoundError",
    "BiblioValidationError",
    "BiblioServerError",
    "BiblioSessionExpiredError",
]
