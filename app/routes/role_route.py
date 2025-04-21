from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, Path, HTTPException, Body, status, Response
from loguru import logger
from tortoise.expressions import Q
from app.handlers.auth import get_current_user
from app.database.models import UserRole, RolePermissionRelation
from app.pydantic_models.roles_models import (
    UserRoleCreateSchema,
    UserRoleEditSchema,
    role_filter_params,
    UserRoleResponseSchema,
    UserRoleListResponseSchema,
    UserRoleSchema,
    UserRoleCreateManySchema
)

role_router = APIRouter()


@role_router.post(
    "/add",
    response_model=UserRoleResponseSchema,
    summary="Добавление новой роли",
    status_code=status.HTTP_201_CREATED
)
async def add_role(
    data: UserRoleCreateSchema = Body(...),
    username: str = Depends(get_current_user)
):
    logger.info(f"Создание роли: {data.dict()}")
    try:
        role = await UserRole.create(role_name=data.role_name)
        logger.success(
            f"Роль {role.role_name} ({role.role_id}) успешно создана")
        return {"role_id": role.role_id}
    except Exception as e:
        logger.exception("Ошибка при создании роли")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@role_router.post(
    "/add-many",
    response_model=UserRoleResponseSchema,
    summary="Добавление новой роли",
    status_code=status.HTTP_201_CREATED
)
async def add_many_roles(
    data: UserRoleCreateManySchema = Body(...),
    username: str = Depends(get_current_user)
):
    logger.info(f"Создание роли: {data.dict()}")
    try:
        role = await UserRole.create(role_name=data.role_name)
        await RolePermissionRelation.bulk_create([
            RolePermissionRelation(role_id=role.role_id,
                                   permission_id=permission_id)
            for permission_id in data.permissions
        ])
        logger.success(
            f"Роль {role.role_name} ({role.role_id}) успешно создана")
        return {"role_id": role.role_id}
    except Exception as e:
        logger.exception("Ошибка при создании роли")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@role_router.patch(
    "/{role_id}",
    response_model=UserRoleResponseSchema,
    summary="Изменение роли"
)
async def edit_role(
    role_id: UUID = Path(..., title="ID роли",
                         description="ID изменяемой роли"),
    data: UserRoleEditSchema = Body(...),
    username: str = Depends(get_current_user)
):
    logger.info(f"Обновление роли {role_id}: {data.dict(exclude_unset=True)}")
    try:
        role = await UserRole.filter(role_id=role_id).first()
        if not role:
            logger.warning(f"Роль {role_id} не найдена")
            raise HTTPException(status_code=404, detail="Роль не найдена")

        if role.role_system_name:
            raise HTTPException(
                status_code=403, detail="Нельзя изменить системную роль"
            )

        await role.update_from_dict(data.dict(exclude_unset=True))
        await role.save()

        logger.success(f"Роль {role_id} успешно обновлена")
        return UserRoleResponseSchema(role_id=role.role_id)
    except Exception as e:
        logger.exception("Ошибка при обновлении роли")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@role_router.delete(
    "/{role_id}",
    summary="Удаление роли",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_role(
    role_id: UUID = Path(..., title="ID роли",
                         description="ID удаляемой роли"),
    username: str = Depends(get_current_user)
):
    logger.info(f"Удаление роли {role_id}")
    try:
        role = await UserRole.filter(role_id=role_id).first()
        if not role:
            logger.warning(f"Роль {role_id} не найдена")
            raise HTTPException(status_code=404, detail="Роль не найдена")

        if role.role_system_name:
            raise HTTPException(
                status_code=403, detail="Нельзя удалить системную роль")

        await role.delete()

        logger.success(f"Роль {role_id} успешно удалена")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        logger.exception(f"Ошибка при удалении роли {role_id}")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@role_router.get(
    "/all",
    response_model=UserRoleListResponseSchema,
    summary="Получение списка ролей с фильтрацией"
)
async def get_roles(
    filters: Annotated[dict, Depends(role_filter_params)],
    username: str = Depends(get_current_user)
):
    logger.info(f"Запрос на список ролей: {filters}")

    try:
        query = Q()
        search_value = filters.get("role_name")
        if search_value:
            query &= Q(role_name__icontains=search_value)

        order_by = f"{'-' if filters.get('order') == 'desc' else ''}{filters.get('sort_by', 'role_name')}"
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        total_count = await UserRole.filter(query).count()

        roles = await UserRole.filter(query).order_by(order_by).offset(
            (page - 1) * page_size
        ).limit(page_size).values("role_id", "role_name")

        if not roles:
            logger.info("Список ролей пуст")

        return UserRoleListResponseSchema(
            total=total_count,
            roles=[UserRoleSchema(**role) for role in roles]
        )
    except Exception as e:
        logger.exception("Ошибка при получении списка ролей")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@role_router.get(
    "/{role_id}",
    response_model=UserRoleSchema,
    summary="Просмотр роли"
)
async def get_role(
    role_id: UUID = Path(..., title="ID роли",
                         description="ID просматриваемой роли"),
    username: str = Depends(get_current_user)
):
    logger.info(f"Запрос на просмотр роли: {role_id}")
    try:
        role = await UserRole.get_or_none(role_id=role_id)
        if role is None:
            logger.warning(f"Роль {role_id} не найдена")
            raise HTTPException(status_code=404, detail="Роль не найдена")

        role_schema = UserRoleSchema(
            role_id=role.role_id,
            role_name=role.role_name,
            role_system_name=role.role_system_name
        )
        logger.success(f"Роль найдена: {role_schema}")
        return role_schema
    except Exception as e:
        logger.exception("Ошибка при просмотре роли")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e
