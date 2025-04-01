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
from app.handlers.auth import get_current_user

relation_router = APIRouter()


@relation_router.post("/add", response_model=UserCompanyRelationResponseSchema, summary="Добавить связь пользователя с компанией", status_code=status.HTTP_201_CREATED)
async def add_user_company_relation(data: UserCompanyRelationCreateSchema, username: str = Depends(get_current_user)):
    try:
        user = await User.get_or_none(user_id=data.user)
        company = await Company.get_or_none(company_id=data.company)
        role = await UserRole.get_or_none(role_id=data.role)

        if not user or not company:
            raise HTTPException(
                status_code=400, detail="Пользователь или компания не найдены")

        relation = await UserCompanyRelation.create(user=user, company=company, role=role)
        return {"user_company_id": str(relation.user_company_id)}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Ошибка при создании связи")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@relation_router.patch("/{user_company_id}", response_model=UserCompanyRelationResponseSchema, summary="Изменить связь пользователя с компанией")
async def update_user_company_relation(user_company_id: UUID, data: UserCompanyRelationEditSchema, username: str = Depends(get_current_user)):
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

    return {"user_company_id": str(relation.user_company_id)}


@relation_router.delete("/{user_company_id}", summary="Удалить связь пользователя с компанией", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_company_relation(user_company_id: UUID, username: str = Depends(get_current_user)):
    relation = await UserCompanyRelation.filter(user_company_id=user_company_id).first()
    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    await relation.delete()
    # return {"message": "Связь удалена"}


@relation_router.get(
    "/all",
    response_model=UserCompanyRelationListResponseSchema,
    summary="Получение списка связей"
)
async def get_user_company_relations(filters: dict = Depends(user_company_filter_params), username: str = Depends(get_current_user)):
    try:
        query = Q()
        if filters.get("user_id"):
            query &= Q(user_id=filters["user_id"])
        if filters.get("company_id"):
            query &= Q(company_id=filters["company_id"])
        if filters.get("role_id"):
            query &= Q(role_id=filters["role_id"])

        # ✅ Общее число записей
        total_count = await UserCompanyRelation.filter(query).count()

        relations = await UserCompanyRelation.filter(query) \
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
                    role_id=relation.role.role_id
                )
                for relation in relations
            ]
        )
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при получении списка связей")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@relation_router.get(
    "/{user_company_id}",
    response_model=UserCompanyRelationSchema,
    summary="Просмотр одной связи"
)
async def get_user_company_relation(user_company_id: UUID, username: str = Depends(get_current_user)):
    relation = await UserCompanyRelation.filter(user_company_id=user_company_id) \
        .prefetch_related("user", "company", "role") \
        .first()

    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    return UserCompanyRelationSchema(
        user_company_id=relation.user_company_id,
        user_id=relation.user.user_id,
        company_id=relation.company.company_id,
        role_id=relation.role.role_id
    )
