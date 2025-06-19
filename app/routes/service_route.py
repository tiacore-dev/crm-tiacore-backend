from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tortoise.expressions import Q

from app.database.models import Service
from app.dependencies.permissions import with_permission_and_service_check
from app.pydantic_models.service_models import (
    ServiceCreateSchema,
    ServiceEditSchema,
    ServiceListResponseSchema,
    ServiceResponseSchema,
    ServiceSchema,
    service_filter_params,
)

service_router = APIRouter()


@service_router.post(
    "/add",
    response_model=ServiceResponseSchema,
    summary="Добавление новой услуги",
    status_code=status.HTTP_201_CREATED,
)
async def add_service(
    data: ServiceCreateSchema = Body(...),
    context: dict = Depends(require_permission_in_context("add_service")),
):
    logger.info(f"Создание услуги: {data.model_dump()}")

    if not context.get("is_superadmin") and (data.company_id != context["company_id"]):
        raise HTTPException(
            status_code=403, detail="Вы не имеете доступа к этой компании"
        )

    service = await Service.create(**data.model_dump())
    if not service:
        logger.error("Не удалось создать услугу")
        raise HTTPException(status_code=500, detail="Не удалось создать услугу")

    logger.success(f"Услуга {service.name} ({service.id}) успешно создана")
    return ServiceResponseSchema(service_id=service.id)


@service_router.patch(
    "/{service_id}", response_model=ServiceResponseSchema, summary="Изменение услуги"
)
async def edit_service(
    service_id: UUID = Path(..., title="ID услуги", description="ID изменяемой услуги"),
    data: ServiceEditSchema = Body(...),
    _=with_permission_and_service_check("edit_service"),
):
    """
    Обновление услуги по ID, переданному в URL.
    """
    logger.info(f"Обновление услуги {service_id}")
    update_data = data.model_dump(exclude_unset=True)
    service = await Service.filter(id=service_id).first()
    if not service:
        logger.warning(f"Услуга {service_id} не найдена")
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    await service.update_from_dict(update_data)

    await service.save()
    logger.success(f"Услуга {service_id} успешно обновлена")
    return ServiceResponseSchema(service_id=service.id)


@service_router.delete(
    "/{service_id}", summary="Удаление услуги", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_service(
    service_id: UUID = Path(..., title="ID услуги", description="ID удаляемой услуги"),
    _=with_permission_and_service_check("delete_service"),
):
    logger.info(f"Удаление услуги {service_id}")

    service = await Service.filter(id=service_id).delete()
    if not service:
        logger.warning(f"Услуга {service_id} не найдена")
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    logger.success(f"Услуга {service_id} успешно удалена")


@service_router.get(
    "/all",
    response_model=ServiceListResponseSchema,
    summary="Получение списка услуг с фильтрацией",
)
async def get_services(
    filters: dict = Depends(service_filter_params),
    context=Depends(require_permission_in_context("get_all_services")),
):
    logger.info(f"Запрос на список услуг: {filters}")

    try:
        query = Q()
        if context["is_superadmin"]:
            company_filter = filters.get("company")
            if company_filter:
                query &= Q(company_id=company_filter)

        else:
            query &= Q(company_id=context["company_id"])

        search_value = filters.get("search")
        if search_value:
            query &= Q(name__icontains=search_value)

        sort_by = filters.get("sort_by", "name")
        if sort_by == "service_name":
            sort_by = "name"

        order = filters.get("order", "asc")
        order_by = f"{'-' if order == 'desc' else ''}{sort_by}"

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        # ✅ Общее число записей
        total_count = await Service.filter(query).count()

        services = (
            await Service.filter(query)
            .order_by(order_by)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .values("id", "name", "company_id")
        )

        return ServiceListResponseSchema(
            total=total_count,
            services=[ServiceSchema(**service) for service in services],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@service_router.get(
    "/{service_id}", response_model=ServiceSchema, summary="Просмотр услуги"
)
async def get_service(
    service_id: UUID = Path(
        ..., title="ID услуги", description="ID просматриваемой услуги"
    ),
    _=with_permission_and_service_check("view_service"),
):
    logger.info(f"Запрос на просмотр услуги: {service_id}")
    try:
        service = (
            await Service.filter(id=service_id)
            .first()
            .values("id", "name", "company_id")
        )
        if service is None:
            logger.warning(f"Услуга {service_id} не найдена")
            raise HTTPException(status_code=404, detail="Услуга не найдена")

        service_schema = ServiceSchema(**service)
        logger.success(f"Услуга найдена: {service_schema}")
        return service_schema

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e
