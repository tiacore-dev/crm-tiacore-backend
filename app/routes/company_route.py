from uuid import UUID
from fastapi import APIRouter, Depends, Path, HTTPException, Body, status
from loguru import logger
from tortoise.expressions import Q
from tortoise.contrib.pydantic import pydantic_model_creator
from app.handlers.auth import get_current_user
from app.database.models import Company
from app.pydantic_models.company_models import (
    CompanyCreateSchema, CompanyEditSchema, company_filter_params, CompanyResponseSchema, CompanyListResponseSchema
)

CompanySchema = pydantic_model_creator(Company, name="CompanySchema")

company_router = APIRouter()


# ✅ 1. Добавление компании
@company_router.post("/add", response_model=CompanyResponseSchema, summary="Добавление новой компании", status_code=status.HTTP_201_CREATED)
async def add_company(data: CompanyCreateSchema = Body(), username: str = Depends(get_current_user)):
    logger.info(f"Создание компании: {data.model_dump()}")
    try:
        company = await Company.create(company_name=data.company_name, description=data.description)

        if not company:
            raise HTTPException(
                status_code=500, detail="Не удалось создать компанию")

        logger.success(f"Компания создана: {company}")
        return {"company_id": str(company.company_id)}

    except Exception as e:
        logger.exception("Ошибка при создании компании")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


# ✅ 2. Изменение компании
@company_router.patch("/{company_id}", response_model=CompanyResponseSchema, summary="Изменение компании")
async def edit_company(
        company_id: UUID = Path(..., title="ID компании",
                                description="ID изменяемой компании"),
        data: CompanyEditSchema = Body(),
        username: str = Depends(get_current_user)):
    logger.info(
        f"Обновление компании {company_id}: {data.model_dump(exclude_unset=True)}")
    try:
        updated_rows = await Company.filter(company_id=company_id).update(**data.model_dump(exclude_unset=True))

        if not updated_rows:
            raise HTTPException(status_code=404, detail="Компания не найдена")

        logger.success(f"Компания {company_id} успешно обновлена")
        return {"company_id": str(company_id)}

    except Exception as e:
        logger.exception("Ошибка при обновлении компании")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


# ✅ 3. Удаление компании
@company_router.delete("/{company_id}", summary="Удаление компании", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
        company_id: UUID = Path(..., title="ID компании",
                                description="ID удаляемой компании"),
        username: str = Depends(get_current_user)):
    logger.info(f"Удаление компании: {company_id}")
    try:
        deleted_count = await Company.filter(company_id=company_id).delete()
        if not deleted_count:
            raise HTTPException(status_code=404, detail="Компания не найдена")

        logger.success(f"Компания {company_id} успешно удалена")
        # return {"detail": "Компания успешно удалена"}

    except Exception as e:
        logger.exception("Ошибка при удалении компании")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@company_router.get(
    "/all",
    response_model=CompanyListResponseSchema,
    summary="Получение списка компаний с фильтрацией"
)
async def get_companies(
    filters: dict = Depends(company_filter_params),
    username: str = Depends(get_current_user)
):
    logger.info(f"Запрос списка компаний: {filters}")

    try:
        query = Q()
        if filters.get("search"):
            query &= Q(company_name__icontains=filters["search"])

        # ✅ Общее число записей
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
                )
                for company in companies
            ]
        )

    except Exception as e:
        logger.exception("Ошибка при получении списка компаний")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


# ✅ 4. Просмотр компании по ID
@company_router.get("/{company_id}", response_model=CompanySchema, summary="Просмотр компании")
async def get_company(
        company_id: UUID = Path(..., title="ID компании",
                                description="ID просматриваемой компании"),
        username: str = Depends(get_current_user)):
    logger.info(f"Запрос на просмотр компании: {company_id}")
    try:
        company = await Company.get_or_none(company_id=company_id)
        if company is None:
            logger.warning(f"Компания {company_id} не найдена")
            raise HTTPException(status_code=404, detail="Компания не найдена")

        company_schema = await CompanySchema.from_tortoise_orm(company)
        logger.success(f"Найдена компания: {company_schema}")
        return company_schema

    except Exception as e:
        logger.exception("Ошибка при просмотре компании")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e
