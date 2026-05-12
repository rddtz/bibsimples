"""
bibsimples - Pacote de Utilitários
===============================

Contém funções auxiliares usadas em todo o projeto.

Módulos:
    - cutter: Gerador de código Cutter-Sanborn
    - marc: Helpers para manipulação de dados MARC
"""

from .cutter import (
    format_author_name,
    generate_book_code,
    generate_cutter_code,
)

__all__ = [
    "generate_cutter_code",
    "generate_book_code",
    "format_author_name",
]
