from uuid import UUID
from fastapi import APIRouter, Depends, Path, HTTPException, Body, status
from loguru import logger
from tortoise.expressions import Q
from app.dependencies.permissions import with_exact_company_permission
from app.handlers.auth import get_current_user, invalidate_user_cache, get_cached_user_data
from app.database.models import Company, UserCompanyRelation,  UserRole, User
from app.pydantic_models.company_models import (
    CompanyCreateSchema, CompanyEditSchema, company_filter_params, CompanyResponseSchema, CompanyListResponseSchema, CompanySchema
)


company_router = APIRouter()


@company_router.post("/add", response_model=CompanyResponseSchema, summary="Добавление новой компании", status_code=status.HTTP_201_CREATED)
async def add_company(data: CompanyCreateSchema = Body(), user_data: dict = Depends(get_current_user)):
    logger.info(f"Создание компании: {data.model_dump()}")
    try:
        company = await Company.create(company_name=data.company_name, description=data.description)

        if not company:
            raise HTTPException(
                status_code=500, detail="Не удалось создать компанию")

        logger.success(f"Компания создана: {company.company_id}")
        role = await UserRole.get_or_none(role_system_name="admin")
        user = await User.get_or_none(email=user_data['email'])
        if role and user:
            await UserCompanyRelation.create(role=role, company=company, user=user)
            # ❗ Подожди, пока связь точно появится
            await user.fetch_related("user_company_relations__role")
            # Теперь инвалидируй и пересоздай кэш
            await invalidate_user_cache(user.email)
            await get_cached_user_data(user.email)

        return {"company_id": str(company.company_id)}

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


# ✅ 2. Изменение компании
@company_router.patch("/{company_id}", response_model=CompanyResponseSchema, summary="Изменение компании")
async def edit_company(
    company_id: UUID = Path(..., title="ID компании",
                            description="ID изменяемой компании"),
    data: CompanyEditSchema = Body(),
        context=with_exact_company_permission("edit_company")):
    logger.info(
        f"Обновление компании {company_id}: {data.model_dump(exclude_unset=True)}")
    try:
        updated_rows = await Company.filter(company_id=company_id).update(**data.model_dump(exclude_unset=True))

        if not updated_rows:
            raise HTTPException(status_code=404, detail="Компания не найдена")

        logger.success(f"Компания {company_id} успешно обновлена")
        return {"company_id": str(company_id)}

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


# ✅ 3. Удаление компании
@company_router.delete("/{company_id}", summary="Удаление компании", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
        company_id: UUID = Path(..., title="ID компании",
                                description="ID удаляемой компании"),
        context=with_exact_company_permission("delete_company")):
    logger.info(f"Удаление компании: {company_id}")
    try:
        deleted_count = await Company.filter(company_id=company_id).delete()
        if not deleted_count:
            raise HTTPException(status_code=404, detail="Компания не найдена")

        logger.success(f"Компания {company_id} успешно удалена")
        user = await User.get_or_none(email=context['email'])
        # ❗ Подожди, пока связь точно появится
        await user.fetch_related("user_company_relations__role")
        # Теперь инвалидируй и пересоздай кэш
        await invalidate_user_cache(user.email)
        await get_cached_user_data(user.email)

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@company_router.get(
    "/all",
    response_model=CompanyListResponseSchema,
    summary="Получение списка компаний с фильтрацией"
)
async def get_companies(
    filters: dict = Depends(company_filter_params),
    user_data: dict = Depends(get_current_user)
):
    logger.info(f"Запрос списка компаний: {filters}")
    try:
        query = Q()

        user = await User.get_or_none(email=user_data['email'])
        if not user:
            raise HTTPException(
                status_code=500, detail="Пользователь не найден в базе")

        if not user.is_superadmin:
            # 🔍 Получаем список компаний, к которым у пользователя есть доступ
            related_company_ids = await UserCompanyRelation.filter(
                user=user
            ).values_list("company__company_id", flat=True)

            if not related_company_ids:
                return CompanyListResponseSchema(total=0, companies=[])

            query &= Q(company_id__in=related_company_ids)

        # 🔎 Фильтрация по названию
        if filters.get("search"):
            query &= Q(company_name__icontains=filters["search"])

        # 📊 Подсчёт и выборка
        total_count = await Company.filter(query).count()

        order_by = f"{'-' if filters.get('order') == 'desc' else ''}{filters.get('sort_by', 'company_name')}"
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        companies = await Company.filter(query) \
            .order_by(order_by) \
            .offset((page - 1) * page_size) \
            .limit(page_size)

        return CompanyListResponseSchema(
            total=total_count,
            companies=[
                CompanySchema(
                    company_id=company.company_id,
                    company_name=company.company_name,
                    description=company.description
                ) for company in companies
            ]
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


# ✅ 4. Просмотр компании по ID
@company_router.get("/{company_id}", response_model=CompanySchema, summary="Просмотр компании")
async def get_company(
        company_id: UUID = Path(..., title="ID компании",
                                description="ID просматриваемой компании"),
        user_data: dict = Depends(get_current_user)
):
    logger.info(f"Запрос на просмотр компании: {company_id}")
    try:
        company = await Company.get_or_none(company_id=company_id)
        if company is None:
            logger.warning(f"Компания {company_id} не найдена")
            raise HTTPException(status_code=404, detail="Компания не найдена")
        user = await User.get_or_none(email=user_data['email'])
        relation = await UserCompanyRelation.filter(user=user, company_id=company_id).exists()
        if not user or (not user.is_superadmin and not relation):

            raise HTTPException(
                status_code=403, detail="Нет доступа к этой компании")

        company_schema = CompanySchema(
            company_id=company.company_id,
            company_name=company.company_name,
            description=company.description
        )

        logger.success(f"Найдена компания: {company_schema}")
        return company_schema

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e
