"""
bibsimples API v1 - Rotas de Catalogação
=====================================

Endpoints para criação de novos livros no Biblivre.
"""

from typing import Any, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.biblivre import BiblioClient, BiblioNotFoundError
from app.utils.cutter import generate_cutter_code, generate_book_code, format_author_name

from .auth import get_biblivre_client

router = APIRouter()


class CreateBookRequest(BaseModel):
    """Dados para catalogação de um novo livro."""

    author_name: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=500)
    cutter_code: Optional[str] = Field(default=None, max_length=20)
    cdd: str = Field(..., min_length=1, max_length=50)
    copies: int = Field(default=1, ge=1, le=200)
    volume: Optional[str] = Field(default=None, max_length=50)


class CreateBookResponse(BaseModel):
    """Resposta da criação de livro."""

    success: bool = True
    message: str
    record_id: int
    database: str
    author_name: str
    title: str
    cdd: str
    cutter_code: str
    volume: str = ""
    holdings_requested: int
    details_url: str = ""


class SimilarRecord(BaseModel):
    """Registro candidato a duplicata, retornado para o usuário decidir."""

    id: int
    title: str = ""
    author: str = ""
    holdings_count: int = 0
    holdings_available: int = 0


class SimilarResponse(BaseModel):
    """Resposta da busca por registros similares."""

    success: bool = True
    matches: list[SimilarRecord] = Field(default_factory=list)


class AddCopiesRequest(BaseModel):
    """Adicionar mais exemplares a um registro existente."""

    copies: int = Field(..., ge=1, le=200)


class AddCopiesResponse(BaseModel):
    """Resposta da adição de exemplares."""

    success: bool = True
    record_id: int
    copies_added: int
    message: str


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _to_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_datafield(
    *,
    ind1: str = " ",
    ind2: str = " ",
    a: str = "",
    b: str = "",
    c: str = "",
) -> dict[str, Any]:
    field: dict[str, Any] = {"ind1": ind1, "ind2": ind2}
    if a:
        field["a"] = [a]
    if b:
        field["b"] = [b]
    if c:
        field["c"] = [c]
    return field


def _build_bibliographic_form_data(
    *,
    author_name: str,
    title: str,
    cdd: str,
    cutter_code: str,
    volume: str,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "100": [_build_datafield(ind1="1", ind2=" ", a=author_name)],
        "245": [_build_datafield(ind1="1", ind2="0", a=title, c=author_name)],
        "082": [_build_datafield(ind1="0", ind2="4", a=cdd)],
        "090": [_build_datafield(ind1=" ", ind2=" ", a=cdd, b=cutter_code, c=volume)],
    }
    return data


def _build_details_url(base_url: str, schema: str, record_id: int) -> str:
    if not base_url or record_id <= 0:
        return ""
    query = urlencode(
        {
            "controller": "json",
            "module": "cataloging.bibliographic",
            "action": "open",
            "id": record_id,
        }
    )
    base = base_url.rstrip("/")
    path = f"{base}/{schema}" if schema else base
    return f"{path}?{query}"


@router.post(
    "/books",
    response_model=CreateBookResponse,
    summary="Catalogar novo livro",
    description=(
        "Cria registro bibliográfico no Biblivre com autor, título, classificação CDD, "
        "Cutter e volume opcional; em seguida cria os exemplares solicitados."
    ),
)
async def create_book(
    payload: CreateBookRequest,
    client: BiblioClient = Depends(get_biblivre_client),
):
    if not client.is_logged_in:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "NotAuthenticated",
                "message": "Faça login antes de catalogar",
            },
        )

    author_name = format_author_name(_normalize_text(payload.author_name))
    title = _normalize_text(payload.title)
    cdd = _normalize_text(payload.cdd)
    volume = _normalize_text(payload.volume)
    cutter_code = _normalize_text(payload.cutter_code) or generate_cutter_code(author_name)
    # Append title letter if not already present (e.g. M149 → M149d)
    if cutter_code and title and not cutter_code[-1].islower():
        articles = ["o ", "a ", "os ", "as ", "um ", "uma ", "the ", "an ", "a "]
        t = title.lower()
        for art in articles:
            if t.startswith(art):
                t = t[len(art):]
                break
        if t:
            cutter_code = f"{cutter_code}{t[0]}"

    bibliographic_data = _build_bibliographic_form_data(
        author_name=author_name,
        title=title,
        cdd=cdd,
        cutter_code=cutter_code,
        volume=volume,
    )

    saved_record = await client.save_record(
        data=bibliographic_data,
        record_id=0,
        data_format="FORM",
        material_type="book",
        database="main",
    )

    record_data = _to_dict(saved_record.get("data"))
    record_id = _to_int(record_data.get("id"), 0)
    if record_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "success": False,
                "error": "CatalogSaveFailed",
                "message": "O Biblivre não retornou um ID de registro válido",
            },
        )

    database = _to_text(record_data.get("database")) or "main"

    await client.create_automatic_holding(
        record_id=record_id,
        database=database,
        holding_count=payload.copies,
        holding_volume_number=0,
        holding_volume_count=1,
        holding_library="",
        holding_acquisition_type="",
        holding_acquisition_date="",
    )

    return CreateBookResponse(
        success=True,
        message="Livro catalogado com sucesso",
        record_id=record_id,
        database=database,
        author_name=author_name,
        title=title,
        cdd=cdd,
        cutter_code=cutter_code,
        volume=volume,
        holdings_requested=payload.copies,
        details_url=_build_details_url(
            base_url=_to_text(getattr(client, "base_url", "")),
            schema=_to_text(getattr(client, "schema", "")) or "default",
            record_id=record_id,
        ),
    )


@router.get(
    "/books/similar",
    response_model=SimilarResponse,
    summary="Buscar registros similares",
    description=(
        "Busca registros existentes no Biblivre que correspondam ao título "
        "(e opcionalmente autor) informado. Usado para evitar registros duplicados "
        "antes de catalogar — se houver matches, o frontend deve perguntar ao "
        "usuário se está adicionando exemplares a um existente."
    ),
)
async def find_similar(
    title: str = Query(..., min_length=1, max_length=500),
    author: str = Query("", max_length=200),
    client: BiblioClient = Depends(get_biblivre_client),
):
    if not client.is_logged_in:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "NotAuthenticated",
                "message": "Faça login antes de catalogar",
            },
        )

    query = " ".join(part for part in (title.strip(), author.strip()) if part)
    if not query:
        return SimilarResponse(matches=[])

    try:
        result = await client.search(query=query, database="main", material_type="all")
    except BiblioNotFoundError:
        return SimilarResponse(matches=[])

    raw_data = _to_dict(result.get("search")).get("data") or []
    matches: list[SimilarRecord] = []
    for item in raw_data[:10]:
        if not isinstance(item, dict):
            continue
        matches.append(
            SimilarRecord(
                id=_to_int(item.get("id"), 0),
                title=_to_text(item.get("title")),
                author=_to_text(item.get("author")),
                holdings_count=_to_int(item.get("holdings_count"), 0),
                holdings_available=_to_int(item.get("holdings_available"), 0),
            )
        )
    return SimilarResponse(matches=matches)


@router.post(
    "/books/{record_id}/copies",
    response_model=AddCopiesResponse,
    summary="Adicionar exemplares a um registro existente",
    description="Cria N exemplares (holdings) para um registro bibliográfico já cadastrado.",
)
async def add_copies(
    record_id: int,
    payload: AddCopiesRequest,
    client: BiblioClient = Depends(get_biblivre_client),
):
    if not client.is_logged_in:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "NotAuthenticated",
                "message": "Faça login antes de adicionar exemplares",
            },
        )

    if record_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "InvalidRecordId",
                "message": "ID de registro inválido",
            },
        )

    await client.create_automatic_holding(
        record_id=record_id,
        database="main",
        holding_count=payload.copies,
        holding_volume_number=0,
        holding_volume_count=1,
        holding_library="",
        holding_acquisition_type="",
        holding_acquisition_date="",
    )

    return AddCopiesResponse(
        success=True,
        record_id=record_id,
        copies_added=payload.copies,
        message=(
            f"{payload.copies} exemplar adicionado com sucesso"
            if payload.copies == 1
            else f"{payload.copies} exemplares adicionados com sucesso"
        ),
    )
