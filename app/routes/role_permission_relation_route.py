from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger

from app.database.models import RolePermissionRelation, UserRole, Permissions, User
from app.pydantic_models.role_permission_relation_models import (
    RolePermissionRelationCreateSchema,
    RolePermissionRelationEditSchema,
    RolePermissionRelationResponseSchema,
    RolePermissionRelationSchema,
    RolePermissionRelationListResponseSchema,
    role_permission_filter_params
)
from app.handlers.auth import require_superadmin, invalidate_user_cache

role_relation_router = APIRouter()


@role_relation_router.post(
    "/add",
    response_model=RolePermissionRelationResponseSchema,
    summary="Добавить связь роль-разрешение", status_code=status.HTTP_201_CREATED
)
async def add_role_permission_relation(
    data: RolePermissionRelationCreateSchema,
    user_data: dict = Depends(require_superadmin)
):
    try:
        role = await UserRole.get_or_none(role_id=data.role)
        permission = await Permissions.get_or_none(permission_id=data.permission)

        if not role or not permission:
            raise HTTPException(
                status_code=400, detail="Роль или разрешение не найдены")

        relation = await RolePermissionRelation.create(role=role, permission=permission)
        return {"role_permission_id": str(relation.role_permission_id)}
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@role_relation_router.patch(
    "/{role_permission_id}",
    response_model=RolePermissionRelationResponseSchema,
    summary="Изменить связь роль-разрешение"
)
async def update_role_permission_relation(
    role_permission_id: UUID,
    data: RolePermissionRelationEditSchema,
    user_data: dict = Depends(require_superadmin)
):
    relation = await RolePermissionRelation.filter(role_permission_id=role_permission_id).first()
    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    update_data = data.dict(exclude_unset=True)

    if "role" in update_data:
        role = await UserRole.get_or_none(role_id=update_data["role"])
        if not role:
            raise HTTPException(status_code=400, detail="Роль не найдена")
        update_data["role"] = role

    if "permission" in update_data:
        permission = await Permissions.get_or_none(permission_id=update_data["permission"])
        if not permission:
            raise HTTPException(
                status_code=400, detail="Разрешение не найдено")
        update_data["permission"] = permission

    await relation.update_from_dict(update_data)
    await relation.save()
    related_users = await User.filter(
        user_company_relations__role=role
    ).distinct()

    for user in related_users:
        await invalidate_user_cache(user.email)

    return {"role_permission_id": str(relation.role_permission_id)}


@role_relation_router.delete(
    "/{role_permission_id}",
    summary="Удалить связь роль-разрешение",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_role_permission_relation(
    role_permission_id: UUID,
    user_data: dict = Depends(require_superadmin)
):
    relation = await RolePermissionRelation.filter(role_permission_id=role_permission_id).first()
    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    await relation.delete()


@role_relation_router.get(
    "/all",
    response_model=RolePermissionRelationListResponseSchema,
    summary="Получение списка связей"
)
async def get_role_permission_relations(
    filters: dict = Depends(role_permission_filter_params),
    user_data: dict = Depends(require_superadmin)
):
    try:
        query = Q()
        if filters.get("role"):
            query &= Q(role_id=filters["role"])
        if filters.get("permission"):
            query &= Q(permission_id=filters["permission"])

        total_count = await RolePermissionRelation.filter(query).count()

        sort_by = filters.get("sort_by", "act_date")
        order = filters.get("order", "asc").lower()
        if order not in ("asc", "desc"):
            raise HTTPException(
                status_code=422, detail="order должен быть 'asc' или 'desc'")

        sort_field = sort_by if order == "asc" else f"-{sort_by}"

        relations = await RolePermissionRelation.filter(query).order_by(sort_field) \
            .prefetch_related("role", "permission") \
            .offset((filters["page"] - 1) * filters["page_size"]) \
            .limit(filters["page_size"])

        return RolePermissionRelationListResponseSchema(
            total=total_count,
            relations=[
                RolePermissionRelationSchema(
                    role_permission_id=rel.role_permission_id,
                    role_id=rel.role.role_id,
                    permission_id=rel.permission.permission_id,
                    created_at=rel.created_at
                ) for rel in relations
            ]
        )
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@role_relation_router.get(
    "/{role_permission_id}",
    response_model=RolePermissionRelationSchema,
    summary="Просмотр одной связи"
)
async def get_role_permission_relation(
    role_permission_id: UUID,
    uuser_data: dict = Depends(require_superadmin)
):
    relation = await RolePermissionRelation.filter(role_permission_id=role_permission_id) \
        .prefetch_related("role", "permission") \
        .first()

    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    return RolePermissionRelationSchema(
        role_permission_id=relation.role_permission_id,
        role_id=relation.role.role_id,
        permission_id=relation.permission.permission_id,
        created_at=relation.created_at
    )
