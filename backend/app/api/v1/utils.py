"""
bibsimples API v1 - Rotas de Utilitários
=====================================

Endpoints para funcionalidades auxiliares.

Endpoints:
    POST /utils/cutter        - Gera código Cutter
    POST /utils/format-author - Formata nome de autor
    POST /utils/book-code     - Gera código completo do livro

Estes endpoints não requerem autenticação no Biblivre.
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.utils.cutter import (
    format_author_name,
    generate_book_code,
    generate_cutter_code,
)

router = APIRouter()


# ==============================================================================
# Schemas
# ==============================================================================

class CutterRequest(BaseModel):
    """Dados para geração de código Cutter."""
    
    author: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nome do autor (qualquer formato)",
        json_schema_extra={"example": "Machado de Assis"}
    )


class CutterResponse(BaseModel):
    """Resposta com código Cutter."""
    
    author: str = Field(
        ...,
        description="Nome do autor original"
    )
    cutter_code: str = Field(
        ...,
        description="Código Cutter gerado",
        json_schema_extra={"example": "M149"}
    )


class FormatAuthorRequest(BaseModel):
    """Dados para formatação de nome."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nome do autor para formatar",
        json_schema_extra={"example": "José de Alencar"}
    )


class FormatAuthorResponse(BaseModel):
    """Resposta com nome formatado."""
    
    original: str = Field(
        ...,
        description="Nome original"
    )
    formatted: str = Field(
        ...,
        description="Nome formatado (Sobrenome, Nome)",
        json_schema_extra={"example": "Alencar, José de"}
    )


class BookCodeRequest(BaseModel):
    """Dados para geração de código de livro."""
    
    author: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nome do autor",
        json_schema_extra={"example": "Machado de Assis"}
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Título do livro",
        json_schema_extra={"example": "Dom Casmurro"}
    )
    classification: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Código de classificação (ex: CDD, CDU)",
        json_schema_extra={"example": "869.0(81)"}
    )
    volume: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Número do volume (se aplicável)",
        json_schema_extra={"example": "v.1"}
    )


class BookCodeResponse(BaseModel):
    """Resposta com código completo do livro."""
    
    cutter_code: str = Field(
        ...,
        description="Código Cutter do autor",
        json_schema_extra={"example": "M149"}
    )
    title_letter: str = Field(
        ...,
        description="Letra inicial do título",
        json_schema_extra={"example": "d"}
    )
    full_code: str = Field(
        ...,
        description="Código completo de chamada",
        json_schema_extra={"example": "869.0(81)\nM149d"}
    )
    classification: Optional[str] = Field(
        default=None,
        description="Classificação usada"
    )
    volume: Optional[str] = Field(
        default=None,
        description="Volume usado"
    )


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post(
    "/cutter",
    response_model=CutterResponse,
    summary="Gerar código Cutter",
    description="""
    Gera o código Cutter-Sanborn para um autor.
    
    O código Cutter é usado em bibliotecas para organizar livros
    por autor. Consiste de uma letra (inicial do sobrenome) seguida
    de números da tabela Cutter-Sanborn.
    
    **Exemplos:**
    - "Machado de Assis" → M149
    - "Silva, João" → S586
    - "José de Alencar" → A353
    
    **Nota:** O algoritmo identifica automaticamente o sobrenome
    principal, tratando partículas (de, da, do) e sufixos (Junior, Filho).
    """,
)
async def generate_cutter(request: CutterRequest):
    """Gera código Cutter para o autor."""
    code = generate_cutter_code(request.author)
    
    return CutterResponse(
        author=request.author,
        cutter_code=code,
    )


@router.post(
    "/format-author",
    response_model=FormatAuthorResponse,
    summary="Formatar nome de autor",
    description="""
    Formata o nome do autor no padrão bibliotecário (AACR2).
    
    Converte do formato direto para o formato invertido:
    - "José de Alencar" → "Alencar, José de"
    - "Machado de Assis" → "Assis, Machado de" (ou mantém se já estiver invertido)
    
    **Regras aplicadas:**
    - Identifica o sobrenome principal
    - Mantém partículas (de, da, do) com o sobrenome
    - Mantém sufixos (Junior, Filho, Neto) com o sobrenome
    """,
)
async def format_author(request: FormatAuthorRequest):
    """Formata nome do autor no padrão bibliotecário."""
    formatted = format_author_name(request.name)
    
    return FormatAuthorResponse(
        original=request.name,
        formatted=formatted,
    )


@router.post(
    "/book-code",
    response_model=BookCodeResponse,
    summary="Gerar código completo do livro",
    description="""
    Gera o código de chamada completo para um livro.
    
    O código de chamada típico inclui:
    1. **Classificação** (opcional) - CDD ou CDU do assunto
    2. **Código Cutter** - Notação do autor
    3. **Letra do título** - Primeira letra significativa
    4. **Volume** (opcional) - Se for obra em múltiplos volumes
    
    **Exemplo:**
    ```
    869.0(81)
    M149d
    v.2
    ```
    
    **Notas:**
    - Artigos no início do título (O, A, Um, The) são ignorados
    - A letra do título é sempre minúscula
    """,
)
async def generate_book(request: BookCodeRequest):
    """Gera código de chamada completo para o livro."""
    # Gera código Cutter
    cutter = generate_cutter_code(request.author)
    
    # Determina letra do título (removendo artigos)
    title_lower = request.title.lower().strip()
    articles = ["o ", "a ", "os ", "as ", "um ", "uma ", "the ", "an ", "a "]
    for article in articles:
        if title_lower.startswith(article):
            title_lower = title_lower[len(article):]
            break
    title_letter = title_lower[0] if title_lower else "x"
    
    # Gera código completo
    full_code = generate_book_code(
        author=request.author,
        title=request.title,
        classification=request.classification,
        volume=request.volume,
    )
    
    return BookCodeResponse(
        cutter_code=cutter,
        title_letter=title_letter,
        full_code=full_code,
        classification=request.classification,
        volume=request.volume,
    )


@router.get(
    "/cutter/{author}",
    response_model=CutterResponse,
    summary="Gerar código Cutter (GET)",
    description="Versão GET do gerador de código Cutter. Use para chamadas simples.",
)
async def generate_cutter_get(
    author: str,
):
    """Gera código Cutter para o autor (via GET)."""
    code = generate_cutter_code(author)
    
    return CutterResponse(
        author=author,
        cutter_code=code,
    )
