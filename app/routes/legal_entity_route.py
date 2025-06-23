from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from tiacore_lib.config import get_settings
from tiacore_lib.handlers.auth_handler import get_current_user
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tiacore_lib.http.http_client import (
    SharedHttpClient,
    get_auth_headers,
)
from tiacore_lib.pydantic_models.legal_entity_models import (
    LegalEntityCreateSchema,
    LegalEntityEditSchema,
    LegalEntityINNCreateSchema,
    LegalEntityListResponseSchema,
    LegalEntityResponseSchema,
    LegalEntitySchema,
    LegalEntityShortSchema,
    inn_kpp_filter_params,
    legal_entity_filter_params,
)

from app.database.models import EntityCompanyRelation
from app.dependencies.permissions import with_permission_and_entity_company_check

entity_router = APIRouter()
http_client = SharedHttpClient()


@entity_router.post(
    "/add",
    response_model=LegalEntityResponseSchema,
    summary="Добавить юридическое лицо",
    status_code=status.HTTP_201_CREATED,
)
async def add_legal_entity(
    request: Request,
    data: LegalEntityCreateSchema,
    _=Depends(require_permission_in_context("add_legal_entity")),
    settings=Depends(get_settings),
):
    headers = get_auth_headers(request)

    response_data, status_code = await http_client.request(
        "POST",
        f"{settings.REFERENCE_URL}/api/legal-entities/add",
        headers=headers,
        json=data.model_dump(),
    )
    return LegalEntityResponseSchema(**response_data)


@entity_router.post(
    "/add-by-inn",
    response_model=LegalEntityResponseSchema,
    summary="Добавить юридическое лицо по ИНН и КПП",
    status_code=status.HTTP_201_CREATED,
)
async def add_legal_entity_by_inn(
    request: Request,
    data: LegalEntityINNCreateSchema,
    _=Depends(require_permission_in_context("add_legal_entity_by_inn")),
    settings=Depends(get_settings),
):
    headers = get_auth_headers(request)

    response_data, status_code = await http_client.request(
        "POST",
        f"{settings.REFERENCE_URL}/api/legal-entities/add-by-inn",
        headers=headers,
        json=data.model_dump(),
    )

    return LegalEntityResponseSchema(**response_data)


@entity_router.patch(
    "/{legal_entity_id}",
    response_model=LegalEntityResponseSchema,
    summary="Изменить юридическое лицо",
)
async def update_legal_entity(
    request: Request,
    legal_entity_id: UUID,
    data: LegalEntityEditSchema,
    _=with_permission_and_entity_company_check("edit_legal_entity"),
    settings=Depends(get_settings),
):
    headers = get_auth_headers(request)

    response_data, status_code = await http_client.request(
        "PATCH",
        f"{settings.REFERENCE_URL}/api/legal-entities/{legal_entity_id}",
        headers=headers,
        json=data.model_dump(),
    )

    return LegalEntityResponseSchema(**response_data)


@entity_router.delete(
    "/{legal_entity_id}",
    summary="Удалить юридическое лицо",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_legal_entity(
    request: Request,
    legal_entity_id: UUID,
    _=with_permission_and_entity_company_check("delete_legal_entity"),
    settings=Depends(get_settings),
):
    headers = get_auth_headers(request)

    _, status_code = await http_client.request(
        "DELETE",
        f"{settings.REFERENCE_URL}/api/legal-entities/{legal_entity_id}",
        headers=headers,
    )
    if status_code != 204:
        raise HTTPException(
            status_code=status_code, detail="Не удалось удалить компанию"
        )


@entity_router.get(
    "/all",
    response_model=LegalEntityListResponseSchema,
    summary="Получение списка юридических лиц",
)
async def get_legal_entities(
    request: Request,
    filters: dict = Depends(legal_entity_filter_params),
    _: dict = Depends(require_permission_in_context("get_all_legal_entities")),
    settings=Depends(get_settings),
):
    headers = get_auth_headers(request)

    # Собираем query-параметры из запроса
    query_params = filters

    response_data, status_code = await http_client.request(
        "GET",
        f"{settings.REFERENCE_URL}/api/legal-entities/all",
        headers=headers,
        params=query_params,
    )
    return LegalEntityListResponseSchema(**response_data)


@entity_router.get(
    "/get-buyers",
    response_model=LegalEntityListResponseSchema,
    summary="Получение списка buyers по локальным связям",
)
async def get_buyers(
    request: Request,
    context: dict = Depends(require_permission_in_context("get_buyers")),
    settings=Depends(get_settings),
):
    # Получаем все id юр. лиц, у которых relation_type == buyer
    legal_entity_ids = await EntityCompanyRelation.filter(
        relation_type="buyer", company_id=context["company_id"]
    ).values_list("legal_entity_id", flat=True)

    if not legal_entity_ids:
        return LegalEntityListResponseSchema(total=0, entities=[])

    headers = get_auth_headers(request)

    # Делаем запрос к reference-сервису
    response_data, status_code = await http_client.request(
        "POST",
        f"{settings.REFERENCE_URL}/api/legal-entities/by-ids",
        headers=headers,
        json={"ids": legal_entity_ids},
    )

    return LegalEntityListResponseSchema(**response_data)


@entity_router.get(
    "/get-sellers",
    response_model=LegalEntityListResponseSchema,
    summary="Получение списка sellers по локальным связям",
)
async def get_sellers(
    request: Request,
    context: dict = Depends(require_permission_in_context("get_sellers")),
    settings=Depends(get_settings),
):
    # Получаем все id юр. лиц, у которых relation_type == buyer
    legal_entity_ids = await EntityCompanyRelation.filter(
        relation_type="seller", company_id=context["company_id"]
    ).values_list("legal_entity_id", flat=True)

    if not legal_entity_ids:
        return LegalEntityListResponseSchema(total=0, entities=[])

    headers = get_auth_headers(request)

    # Делаем запрос к reference-сервису
    response_data, status_code = await http_client.request(
        "POST",
        f"{settings.REFERENCE_URL}/api/legal-entities/by-ids",
        headers=headers,
        json={"ids": legal_entity_ids},
    )

    return LegalEntityListResponseSchema(**response_data)


@entity_router.get(
    "/get-by-company",
    response_model=LegalEntityListResponseSchema,
    summary="Получение списка организаций по компании",
)
async def get_by_company(
    request: Request,
    company_id: UUID = Query(..., description="ID компании"),
    _: dict = Depends(require_permission_in_context("get_by_company")),
    settings=Depends(get_settings),
):
    # Получаем все id юр. лиц, у которых relation_type == buyer
    legal_entity_ids = await EntityCompanyRelation.filter(
        company_id=company_id
    ).values_list("legal_entity_id", flat=True)

    if not legal_entity_ids:
        return LegalEntityListResponseSchema(total=0, entities=[])

    headers = get_auth_headers(request)

    # Делаем запрос к reference-сервису
    response_data, status_code = await http_client.request(
        "POST",
        f"{settings.REFERENCE_URL}/api/legal-entities/by-ids",
        headers=headers,
        json={"ids": legal_entity_ids},
    )

    return LegalEntityListResponseSchema(**response_data)


@entity_router.get(
    "/inn-kpp",
    response_model=LegalEntityShortSchema,
    summary="Получение организации по инн и кпп",
)
async def get_legal_entity_by_inn_kpp(
    request: Request,
    filters: dict[str, Optional[str]] = Depends(inn_kpp_filter_params),
    _: dict = Depends(get_current_user),
    settings=Depends(get_settings),
):
    headers = get_auth_headers(request)

    # Собираем query-параметры из запроса
    query_params = filters

    response_data, status_code = await http_client.request(
        "GET",
        f"{settings.REFERENCE_URL}/api/legal-entities/all",
        headers=headers,
        params=query_params,
    )
    return LegalEntityShortSchema(**response_data)


@entity_router.get(
    "/{legal_entity_id}",
    response_model=LegalEntitySchema,
    summary="Просмотр одного юридического лица",
)
async def get_legal_entity(
    request: Request,
    legal_entity_id: UUID,
    context: dict = Depends(require_permission_in_context("view_legal_entity")),
    settings=Depends(get_settings),
):
    headers = get_auth_headers(request)

    response_data, status_code = await http_client.request(
        "GET",
        f"{settings.REFERENCE_URL}/api/legal-entities/{legal_entity_id}",
        headers=headers,
    )
    return LegalEntitySchema(**response_data)
