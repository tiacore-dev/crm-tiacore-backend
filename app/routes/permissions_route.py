from typing import Annotated
from fastapi import APIRouter, Depends, Path, HTTPException, Body, status, Response
from loguru import logger
from tortoise.expressions import Q
from app.handlers.auth import get_current_user
from app.database.models import Permissions
from app.pydantic_models.permissions_models import (
    PermissionsCreateSchema,
    PermissionsEditSchema,
    permission_filter_params,
    PermissionsResponseSchema,
    PermissionsListResponseSchema,
    PermissionsSchema
)

permissions_router = APIRouter()


@permissions_router.post(
    "/add",
    response_model=PermissionsResponseSchema,
    summary="Добавление нового разрешения",
    status_code=status.HTTP_201_CREATED
)
async def add_permission(
    data: PermissionsCreateSchema = Body(...),
    username: str = Depends(get_current_user)
):
    logger.info(f"Создание разрешения: {data.dict()}")
    try:
        permission = await Permissions.create(**data.dict())
        logger.success(
            f"Разрешение {permission.permission_id} успешно создано")
        return {"permission_id": permission.permission_id}
    except Exception as e:
        logger.exception("Ошибка при создании разрешения")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@permissions_router.patch(
    "/{permission_id}",
    response_model=PermissionsResponseSchema,
    summary="Изменение разрешения"
)
async def edit_permission(
    permission_id: str = Path(..., title="ID разрешения",
                              description="ID изменяемого разрешения"),
    data: PermissionsEditSchema = Body(...),
    username: str = Depends(get_current_user)
):
    logger.info(
        f"Обновление разрешения {permission_id}: {data.dict(exclude_unset=True)}")
    try:
        updated_rows = await Permissions.filter(permission_id=permission_id).update(**data.dict(exclude_unset=True))
        if not updated_rows:
            logger.warning(f"Разрешение {permission_id} не найдено")
            raise HTTPException(
                status_code=404, detail="Разрешение не найдено")

        logger.success(f"Разрешение {permission_id} успешно обновлено")
        return {"permission_id": permission_id}
    except Exception as e:
        logger.exception("Ошибка при обновлении разрешения")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@permissions_router.delete(
    "/{permission_id}",
    summary="Удаление разрешения",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_permission(
    permission_id: str = Path(..., title="ID разрешения",
                              description="ID удаляемого разрешения"),
    username: str = Depends(get_current_user)
):
    logger.info(f"Удаление разрешения {permission_id}")
    try:
        deleted_count = await Permissions.filter(permission_id=permission_id).delete()
        if not deleted_count:
            logger.warning(f"Разрешение {permission_id} не найдено")
            raise HTTPException(
                status_code=404, detail="Разрешение не найдено")

        logger.success(f"Разрешение {permission_id} успешно удалено")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.exception("Ошибка при удалении разрешения")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


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
    except Exception as e:
        logger.exception("Ошибка при получении списка разрешений")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@permissions_router.get(
    "/{permission_id}",
    response_model=PermissionsSchema,
    summary="Просмотр разрешения"
)
async def get_permission(
    permission_id: str = Path(..., title="ID разрешения",
                              description="ID просматриваемого разрешения"),
    username: str = Depends(get_current_user)
):
    logger.info(f"Запрос на просмотр разрешения: {permission_id}")
    try:
        permission = await Permissions.get_or_none(permission_id=permission_id)
        if permission is None:
            logger.warning(f"Разрешение {permission_id} не найдено")
            raise HTTPException(
                status_code=404, detail="Разрешение не найдено")

        permission_schema = PermissionsSchema(
            permission_id=permission.permission_id,
            permission_name=permission.permission_name,
            comment=permission.comment
        )
        logger.success(f"Разрешение найдено: {permission_schema}")
        return permission_schema
    except Exception as e:
        logger.exception("Ошибка при просмотре разрешения")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e
