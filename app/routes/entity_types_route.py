from fastapi import APIRouter, Depends, Request
from tiacore_lib.config import get_settings
from tiacore_lib.handlers.auth_handler import get_current_user
from tiacore_lib.http.http_client import (
    SharedHttpClient,
    get_auth_headers,
)
from tiacore_lib.pydantic_models.entity_type_models import (
    FilterParams,
    LegalEntityTypeListResponse,
)

http_client = SharedHttpClient()
entity_types_router = APIRouter()


@entity_types_router.get(
    "/all",
    response_model=LegalEntityTypeListResponse,
    summary="Получение списка типов юр. лиц с фильтрацией",
)
async def get_entity_types(
    request: Request,
    filters: FilterParams = Depends(),
    _: str = Depends(get_current_user),
    settings=Depends(get_settings),
):
    headers = get_auth_headers(request)

    # Собираем query-параметры из запроса
    query_params = filters

    response_data, status_code = await http_client.request(
        "GET",
        f"{settings.REFERENCE_URL}/api/legal-entity-types/all",
        headers=headers,
        params=query_params,
    )
    return LegalEntityTypeListResponse(**response_data)
