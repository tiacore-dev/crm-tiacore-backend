from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from tortoise.expressions import Q
from app.handlers.auth import get_current_user
from app.database.models import Permissions
from app.pydantic_models.permissions_models import (
    permission_filter_params,
    PermissionsListResponseSchema,
    PermissionsSchema
)

permissions_router = APIRouter()


@permissions_router.get(
    "/all",
    response_model=PermissionsListResponseSchema,
    summary="Получение списка разрешений с фильтрацией"
)
async def get_permissions(
    filters: Annotated[dict, Depends(permission_filter_params)],
    username: str = Depends(get_current_user)
):
    logger.info(f"Запрос на список разрешений: {filters}")

    try:
        query = Q()
        if filters.get("comment"):
            query &= Q(comment__icontains=filters["comment"])
        if filters.get("permission_name"):
            query &= Q(comment__icontains=filters["permission_name"])

        order_by = f"{'-' if filters.get('order') == 'desc' else ''}{filters.get('sort_by', 'permission_id')}"
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        total_count = await Permissions.filter(query).count()

        permissions = await Permissions.filter(query).order_by(order_by).offset(
            (page - 1) * page_size
        ).limit(page_size).values("permission_id", "permission_name", "comment")

        if not permissions:
            logger.info("Список разрешений пуст")

        return PermissionsListResponseSchema(
            total=total_count,
            permissions=[PermissionsSchema(**p) for p in permissions]
        )
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e
