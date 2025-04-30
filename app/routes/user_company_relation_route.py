from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import UserCompanyRelation, User, Company, UserRole
from app.pydantic_models.user_company_relation_models import (
    UserCompanyRelationCreateSchema,
    UserCompanyRelationResponseSchema,
    UserCompanyRelationEditSchema,
    user_company_filter_params,
    UserCompanyRelationSchema,
    UserCompanyRelationListResponseSchema
)
from app.handlers.depends import require_permission_in_context
from app.dependencies.permissions import with_permission_and_user_company_check
from app.handlers.auth import invalidate_user_cache, get_cached_user_data

relation_router = APIRouter()


@relation_router.post(
    "/add",
    response_model=UserCompanyRelationResponseSchema,
    summary="Добавить связь пользователя с компанией",
    status_code=status.HTTP_201_CREATED
)
async def add_user_company_relation(
        data: UserCompanyRelationCreateSchema,
        context: dict = Depends(
            require_permission_in_context("add_user_company_relation"))
):
    try:
        user = await User.get_or_none(user_id=data.user)
        company = await Company.get_or_none(company_id=data.company)
        role = await UserRole.get_or_none(role_id=data.role)

        if not user or not company:
            raise HTTPException(
                status_code=400, detail="Пользователь или компания не найдены")
        if not context.get("is_superadmin"):
            is_related = await UserCompanyRelation.exists(user_id=context["user"], company=company)
            if not is_related:
                raise HTTPException(
                    status_code=403,
                    detail="Вы не имеете доступа к этой компании"
                )

        relation = await UserCompanyRelation.create(user=user, company=company, role=role)
        await invalidate_user_cache(user.email)
        await get_cached_user_data(user.email)
        return {"user_company_id": str(relation.user_company_id)}
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@relation_router.patch(
    "/{user_company_id}",
    response_model=UserCompanyRelationResponseSchema,
    summary="Изменить связь пользователя с компанией"
)
async def update_user_company_relation(
    user_company_id: UUID,
    data: UserCompanyRelationEditSchema,
    context=with_permission_and_user_company_check(
        "edit_user_company_relation")
):
    relation = await UserCompanyRelation.filter(user_company_id=user_company_id).first()
    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    update_data = data.dict(exclude_unset=True)

    # Загружаем объекты, если переданы новые ID
    if "user" in update_data:
        user = await User.get_or_none(user_id=update_data["user"])
        if not user:
            raise HTTPException(
                status_code=400, detail="Пользователь не найден")
        update_data["user"] = user

    if "company" in update_data:
        company = await Company.get_or_none(company_id=update_data["company"])
        if not company:
            raise HTTPException(status_code=400, detail="Компания не найдена")
        update_data["company"] = company

    if "role" in update_data:
        role = await UserRole.get_or_none(role_id=update_data["role"])
        if not role:
            raise HTTPException(status_code=400, detail="Роль не найдена")
        update_data["role"] = role

    # Обновляем связь
    await relation.update_from_dict(update_data)
    await relation.save()
    await relation.fetch_related("user")  # чтобы relation.user был доступен
    await invalidate_user_cache(relation.user.email)
    await get_cached_user_data(relation.user.email)

    return {"user_company_id": str(relation.user_company_id)}


@relation_router.delete(
    "/{user_company_id}",
    summary="Удалить связь пользователя с компанией",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user_company_relation(
    user_company_id: UUID,
    context=with_permission_and_user_company_check(
        "delete_user_company_relation")):
    relation = await UserCompanyRelation.filter(user_company_id=user_company_id).prefetch_related("user").first()
    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")
    await relation.delete()
    await invalidate_user_cache(relation.user.email)
    await get_cached_user_data(relation.user.email)


@relation_router.get(
    "/all",
    response_model=UserCompanyRelationListResponseSchema,
    summary="Получение списка связей"
)
async def get_user_company_relations(
    filters: dict = Depends(user_company_filter_params),
    context: dict = Depends(
        require_permission_in_context("get_all_user_company_relations"))
):
    try:
        query = Q()
        if filters.get("user"):
            query &= Q(user=filters["user"])
        if context["is_superadmin"]:
            company_filter = filters.get("company")
            if company_filter:
                query &= Q(company_id=company_filter)
        else:
            query &= Q(company_id=context['company'])
        if filters.get("role"):
            query &= Q(role=filters["role"])

        sort_by = filters.get("sort_by", "act_date")
        order = filters.get("order", "asc").lower()
        if order not in ("asc", "desc"):
            raise HTTPException(
                status_code=422, detail="order должен быть 'asc' или 'desc'")

        sort_field = sort_by if order == "asc" else f"-{sort_by}"

        # ✅ Общее число записей
        total_count = await UserCompanyRelation.filter(query).count()

        relations = await UserCompanyRelation.filter(query).order_by(sort_field) \
            .prefetch_related("user", "company", "role") \
            .offset((filters["page"] - 1) * filters["page_size"]) \
            .limit(filters["page_size"])

        return UserCompanyRelationListResponseSchema(
            total=total_count,
            relations=[
                UserCompanyRelationSchema(
                    user_company_id=relation.user_company_id,
                    user_id=relation.user.user_id,
                    company_id=relation.company.company_id,
                    role_id=relation.role.role_id,
                    created_at=relation.created_at
                )
                for relation in relations
            ]
        )
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@relation_router.get(
    "/{user_company_id}",
    response_model=UserCompanyRelationSchema,
    summary="Просмотр одной связи"
)
async def get_user_company_relation(
    user_company_id: UUID,
    context=with_permission_and_user_company_check(
        "view_user_company_relation")
):
    relation = await UserCompanyRelation.filter(user_company_id=user_company_id) \
        .prefetch_related("user", "company", "role") \
        .first()

    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    return UserCompanyRelationSchema(
        user_company_id=relation.user_company_id,
        user_id=relation.user.user_id,
        company_id=relation.company.company_id,
        role_id=relation.role.role_id,
        created_at=relation.created_at
    )
