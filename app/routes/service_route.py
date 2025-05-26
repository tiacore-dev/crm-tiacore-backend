from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from loguru import logger
from tortoise.expressions import Q

from app.database.models import Company, Service, UserCompanyRelation
from app.dependencies.permissions import with_permission_and_service_check
from app.handlers.depends import require_permission_in_context
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
    try:
        company = await Company.get_or_none(company_id=data.company)
        if not company:
            logger.warning(
                f"Попытка создать услугу с несуществующей компанией: {data.company}"
            )
            raise HTTPException(status_code=400, detail="Компания не найдена")

        if not context.get("is_superadmin"):
            is_related = await UserCompanyRelation.exists(
                user_id=context["user"], company=company
            )
            if not is_related:
                raise HTTPException(
                    status_code=403, detail="Вы не имеете доступа к этой компании"
                )

        service = await Service.create(service_name=data.service_name, company=company)
        if not service:
            logger.error("Не удалось создать услугу")
            raise HTTPException(status_code=500, detail="Не удалось создать услугу")

        logger.success(
            f"Услуга {service.service_name} ({service.service_id}) успешно создана"
        )
        return {"service_id": str(service.service_id)}
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


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
    logger.info(
        f"Обновление услуги {service_id}: {data.model_dump(exclude_unset=True)}"
    )
    try:
        # update(**data.model_dump(exclude_unset=True))
        service = await Service.filter(service_id=service_id).first()

        if not service:
            logger.warning(f"Услуга {service_id} не найдена")
            raise HTTPException(status_code=404, detail="Услуга не найдена")
        if data.company is not None:
            company = await Company.get_or_none(company_id=data.company)
            if not company:
                logger.warning(
                    f"Попытка создать услугу с несуществующей компанией: {data.company}"
                )
                raise HTTPException(status_code=400, detail="Компания не найдена")
            service.company = company
        if data.service_name:
            service.service_name = data.service_name
        await service.save()
        logger.success(f"Услуга {service_id} успешно обновлена")
        return {"service_id": str(service_id)}
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@service_router.delete(
    "/{service_id}", summary="Удаление услуги", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_service(
    service_id: UUID = Path(..., title="ID услуги", description="ID удаляемой услуги"),
    _=with_permission_and_service_check("delete_service"),
):
    logger.info(f"Удаление услуги {service_id}")
    try:
        deleted_count = await Service.filter(service_id=service_id).delete()
        if not deleted_count:
            logger.warning(f"Услуга {service_id} не найдена")
            raise HTTPException(status_code=404, detail="Услуга не найдена")

        logger.success(f"Услуга {service_id} успешно удалена")

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


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
            query &= Q(company_id=context["company"])

        search_value = filters.get("search")
        if search_value:
            query &= Q(service_name__icontains=search_value)

        order_by = f"{'-' if filters.get('order') == 'desc' else ''}{
            filters.get('sort_by', 'service_name')
        }"
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        # ✅ Общее число записей
        total_count = await Service.filter(query).count()

        services = (
            await Service.filter(query)
            .order_by(order_by)
            .offset(
                (page - 1) * page_size
                # ✅ Достаём сразу в виде словарей
            )
            .limit(page_size)
            .values("service_id", "service_name", "company_id")
        )

        return ServiceListResponseSchema(
            total=total_count,
            services=[
                ServiceSchema(
                    service_id=service["service_id"],
                    service_name=service["service_name"],
                    company=service["company_id"],
                )
                for service in services
            ],
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
        service = await Service.get_or_none(service_id=service_id).prefetch_related(
            "company"
        )
        if service is None:
            logger.warning(f"Услуга {service_id} не найдена")
            raise HTTPException(status_code=404, detail="Услуга не найдена")

        # ✅ Создаём Pydantic-схему из ORM-модели
        service_schema = ServiceSchema(
            service_id=service.service_id,
            service_name=service.service_name,
            company=service.company.company_id,
        )
        logger.success(f"Услуга найдена: {service_schema}")
        return service_schema

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e
