from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Path, HTTPException
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
async def add_service(data: ServiceCreateSchema, username: str = Depends(get_current_user)):
    try:
        service = await Service.create(service_name=data.service_name)
        if not service:
            raise HTTPException(
                status_code=500, detail="Не удалось создать услугу")
        return {"service_id": str(service.service_id)}
    except Exception as e:
        logger.error(f"Ошибка при создании услуги: {e}")
        return None


@service_router.patch("/{service_id}/edit", response_model=ServiceResponseSchema, summary="Изменение услуги")
async def edit_service(
        service_id: str = Path(..., title="ID услуги",
                               description="ID изменяемой услуги"),
        data: ServiceEditSchema = Depends(),  # Передача данных через тело запроса
        username: str = Depends(get_current_user)):
    """
    Обновление услуги по ID, переданному в URL.
    """
    try:
        updated_rows = await Service.filter(service_id=service_id).update(**data.dict(exclude_unset=True))

        if not updated_rows:
            raise HTTPException(status_code=404, detail="Услуга не найдена")

        # Возвращаем обновлённый объект
        return {"service_id": service_id}
    except Exception as e:
        logger.error(f"Ошибка при создании услуги: {e}")
        return None


@service_router.delete("/{service_id}/delete", summary="Удаление услуги")
async def delete_service(
        service_id: str = Path(..., title="ID услуги",
                               description="ID удаляемой услуги"),
        username: str = Depends(get_current_user)):
    try:
        await Service.filter(service_id=service_id).delete()
        return
    except Exception as e:
        logger.error(f"Ошибка при удалении услуги: {e}")
        return None


@service_router.get("/{service_id}/view", response_model=ServiceSchema, summary="Просмотр услуги")
async def get_service(
    service_id: str = Path(..., title="ID услуги",
                           description="ID просматриваемой услуги"),
    username: str = Depends(get_current_user)
):
    try:
        logger.info(f"Получен запрос на просмотр услуги: {service_id}")

        # Проверяем, корректен ли UUID
        try:
            service_uuid = UUID(service_id)
        except ValueError as exc:
            logger.error(f"Некорректный UUID: {service_id}")
            raise HTTPException(
                status_code=400, detail="Некорректный формат ID услуги") from exc

        # Получаем объект услуги
        service = await Service.get_or_none(service_id=service_uuid)
        if service is None:
            logger.warning(f"Услуга {service_uuid} не найдена")
            raise HTTPException(status_code=404, detail="Услуга не найдена")

        logger.info(f"Найдена услуга: {service}")

        # Используем правильную конвертацию
        service_schema = await ServiceSchema.from_tortoise_orm(service)
        logger.info(f"Успешно конвертировано: {service_schema}")
        return service_schema

    except Exception as e:
        logger.exception(f"Ошибка при просмотре услуги: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@service_router.get("/all", response_model=List[ServiceSchema], summary="Получение списка услуг с фильтрацией")
async def get_services(
    filters: dict = Depends(service_filter_params),
    username: str = Depends(get_current_user)
):
    try:
        logger.info(f"Получен запрос на список услуг: {filters}")

        # Формируем динамический фильтр
        query = Q()
        if filters.search:
            # Частичный поиск
            query &= Q(service_name__icontains=filters.search)

        # Определяем порядок сортировки
        order_by = f"{'-' if filters.order == 'desc' else ''}{filters.sort_by}"

        # Запрашиваем данные с фильтрацией, сортировкой и пагинацией
        services = await Service.filter(query).order_by(order_by).offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

        # Конвертируем в Pydantic
        service_list = [await ServiceSchema.from_tortoise_orm(service) for service in services]

        logger.info(
            f"Найдено {len(service_list)} услуг (страница {filters.page})")
        return service_list

    except Exception as e:
        logger.exception(f"Ошибка при получении списка услуг: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e
