from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Path, HTTPException, Body
from loguru import logger
from tortoise.expressions import Q
from tortoise.contrib.pydantic import pydantic_model_creator
from app.handlers.auth import get_current_user
from app.database.models import Service
from app.pydantic_models.service_models import (
    ServiceCreateSchema, ServiceEditSchema, service_filter_params, ServiceResponseSchema
)

ServiceSchema = pydantic_model_creator(Service, name="ServiceSchema")

service_router = APIRouter()


@service_router.post("/add", response_model=ServiceResponseSchema, summary="Добавление новой услуги")
async def add_service(data: ServiceCreateSchema = Body(...), username: str = Depends(get_current_user)):
    logger.info(f"Создание услуги: {data.dict()}")
    try:
        service = await Service.create(service_name=data.service_name)
        if not service:
            logger.error("Не удалось создать услугу")
            raise HTTPException(
                status_code=500, detail="Не удалось создать услугу")

        logger.success(
            f"Услуга {service.service_name} ({service.service_id}) успешно создана")
        return {"service_id": str(service.service_id)}
    except Exception as e:
        logger.exception("Ошибка при создании услуги")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@service_router.patch("/{service_id}", response_model=ServiceResponseSchema, summary="Изменение услуги")
async def edit_service(
        service_id: UUID = Path(..., title="ID услуги",
                                description="ID изменяемой услуги"),
        data: ServiceEditSchema = Body(...),
        username: str = Depends(get_current_user)):
    """
    Обновление услуги по ID, переданному в URL.
    """
    logger.info(
        f"Обновление услуги {service_id}: {data.dict(exclude_unset=True)}")
    try:
        updated_rows = await Service.filter(service_id=service_id).update(**data.dict(exclude_unset=True))

        if not updated_rows:
            logger.warning(f"Услуга {service_id} не найдена")
            raise HTTPException(status_code=404, detail="Услуга не найдена")

        logger.success(f"Услуга {service_id} успешно обновлена")
        return {"service_id": str(service_id)}
    except Exception as e:
        logger.exception("Ошибка при обновлении услуги")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@service_router.delete("/{service_id}", summary="Удаление услуги")
async def delete_service(
        service_id: UUID = Path(..., title="ID услуги",
                                description="ID удаляемой услуги"),
        username: str = Depends(get_current_user)):
    logger.info(f"Удаление услуги {service_id}")
    try:
        deleted_count = await Service.filter(service_id=service_id).delete()
        if not deleted_count:
            logger.warning(f"Услуга {service_id} не найдена")
            raise HTTPException(status_code=404, detail="Услуга не найдена")

        logger.success(f"Услуга {service_id} успешно удалена")
        return {"detail": "Услуга успешно удалена"}
    except Exception as e:
        logger.exception("Ошибка при удалении услуги")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@service_router.get("/all", response_model=List[ServiceSchema], summary="Получение списка услуг с фильтрацией")
async def get_services(
    filters: dict = Depends(service_filter_params),
    username: str = Depends(get_current_user)
):
    logger.info(f"Запрос на список услуг: {filters}")

    try:
        query = Q()
        # ✅ Теперь получаем данные из dict
        search_value = filters.get("search")
        if search_value:
            query &= Q(service_name__icontains=search_value)

        order_by = f"{'-' if filters['order'] == 'desc' else ''}{filters['sort_by']}"

        services = await Service.filter(query).order_by(order_by).offset(
            (filters["page"] - 1) * filters["page_size"]
        ).limit(filters["page_size"])

        service_list = [await ServiceSchema.from_tortoise_orm(service) for service in services]

        logger.success(
            f"Найдено {len(service_list)} услуг (страница {filters['page']})")
        return service_list
    except Exception as e:
        logger.exception("Ошибка при получении списка услуг")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@service_router.get("/{service_id}", response_model=ServiceSchema, summary="Просмотр услуги")
async def get_service(
    service_id: UUID = Path(..., title="ID услуги",
                            description="ID просматриваемой услуги"),
    username: str = Depends(get_current_user)
):
    logger.info(f"Запрос на просмотр услуги: {service_id}")
    try:
        service = await Service.get_or_none(service_id=service_id)
        if service is None:
            logger.warning(f"Услуга {service_id} не найдена")
            raise HTTPException(status_code=404, detail="Услуга не найдена")

        service_schema = await ServiceSchema.from_tortoise_orm(service)
        logger.success(f"Услуга найдена: {service_schema}")
        return service_schema
    except Exception as e:
        logger.exception("Ошибка при просмотре услуги")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e
