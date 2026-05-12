"""
bibsimples API v1 - Rotas de Pesquisa
==================================

Endpoints para busca no acervo do Biblivre.
"""

from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.biblivre import BiblioClient, BiblioNotFoundError

from .auth import get_biblivre_client

router = APIRouter()


class SearchField(BaseModel):
    """Campo retornado pelo Biblivre."""

    field: str
    value: str


class SearchRecord(BaseModel):
    """Registro simplificado de busca."""

    id: int
    database: str = "main"
    title: str = ""
    author: str = ""
    year: str = ""
    holdings_count: int = 0
    holdings_available: int = 0
    holdings_lent: int = 0
    details_url: str = ""
    fields: list[SearchField] = Field(default_factory=list)


class SearchData(BaseModel):
    """Metadados e itens da busca."""

    id: int = 0
    record_count: int = 0
    page: int = 1
    pages: int = 0
    data: list[SearchRecord] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Resposta de busca."""

    success: bool = True
    query: str
    search: SearchData


def _field_value(fields: list[dict[str, Any]], name: str) -> str:
    """Extrai valor de um campo específico."""
    for item in fields:
        if item.get("field") == name:
            return _to_text(item.get("value"))
    return ""


def _to_text(value: Any) -> str:
    """Converte valor para texto seguro."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _to_int(value: Any, default: int = 0) -> int:
    """Converte valor para inteiro com fallback."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_dict(value: Any) -> dict[str, Any]:
    """Garante dicionário."""
    return value if isinstance(value, dict) else {}


def _to_list(value: Any) -> list[Any]:
    """Garante lista."""
    return value if isinstance(value, list) else []


def _normalize_record(raw_record: dict[str, Any]) -> SearchRecord:
    """Normaliza o formato de registro retornado pelo Biblivre."""
    fields_list = _to_list(raw_record.get("fields"))

    title = raw_record.get("title")
    if not isinstance(title, str) or not title:
        title = _field_value(fields_list, "title")

    author = raw_record.get("author")
    if not isinstance(author, str) or not author:
        author = _field_value(fields_list, "author")

    year = raw_record.get("year")
    if not isinstance(year, str) or not year:
        year = _field_value(fields_list, "year") or _field_value(
            fields_list, "publication_year"
        )

    normalized_fields = [
        SearchField(
            field=_to_text(item.get("field")),
            value=_to_text(item.get("value")),
        )
        for item in fields_list
        if isinstance(item, dict)
    ]

    return SearchRecord(
        id=_to_int(raw_record.get("id"), 0),
        database=_to_text(raw_record.get("database")) or "main",
        title=title,
        author=author,
        year=year,
        holdings_count=_to_int(raw_record.get("holdings_count"), 0),
        holdings_available=_to_int(raw_record.get("holdings_available"), 0),
        holdings_lent=_to_int(raw_record.get("holdings_lent"), 0),
        fields=normalized_fields,
    )


def _build_details_url(base_url: str, schema: str, record_id: int) -> str:
    """Monta URL de detalhes do registro no Biblivre."""
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
    return f"{base_url.rstrip('/')}/{schema}?{query}"


@router.get(
    "",
    response_model=SearchResponse,
    summary="Pesquisar no acervo",
    description="Executa busca simples no acervo do Biblivre.",
)
async def search_catalog(
    query: str = Query(..., min_length=1, description="Termo de pesquisa"),
    database: str = Query("main", description='Base: "main", "work", "private", "trash"'),
    material_type: str = Query("all", description='Tipo: "all", "book", etc.'),
    client: BiblioClient = Depends(get_biblivre_client),
):
    """Pesquisa no acervo autenticado do Biblivre."""
    if not client.is_logged_in:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "NotAuthenticated",
                "message": "Faça login antes de pesquisar",
            },
        )

    try:
        result = await client.search(
            query=query,
            database=database,
            material_type=material_type,
        )
    except BiblioNotFoundError:
        return SearchResponse(
            success=True,
            query=query,
            search=SearchData(
                record_count=0,
                page=1,
                pages=0,
                data=[],
            ),
        )

    search_payload = _to_dict(result.get("search"))
    raw_data = _to_list(search_payload.get("data"))
    client_base_url = _to_text(getattr(client, "base_url", ""))
    client_schema = _to_text(getattr(client, "schema", "")) or "default"

    records: list[SearchRecord] = []
    for item in raw_data:
        if not isinstance(item, dict):
            continue
        record = _normalize_record(item)
        record.details_url = _build_details_url(
            base_url=client_base_url,
            schema=client_schema,
            record_id=record.id,
        )
        records.append(record)

    record_count = _to_int(search_payload.get("record_count"), len(records))
    page = _to_int(search_payload.get("page"), 1)
    pages = _to_int(search_payload.get("pages"), 1 if record_count > 0 else 0)

    return SearchResponse(
        success=True,
        query=query,
        search=SearchData(
            id=_to_int(search_payload.get("id"), 0),
            record_count=record_count,
            page=page,
            pages=pages,
            data=records,
        ),
    )
