from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import BillDetails, Bills, Service, EntityCompanyRelation
from app.pydantic_models.bill_detail_models import (
    BillDetailCreateSchema,
    BillDetailResponseSchema,
    BillDetailEditSchema,
    BillDetailSchema,
    bill_detail_filter_params,
    BillDetailListResponseSchema
)
from app.dependencies.permissions import with_permission_through_bill
from app.handlers.depends import require_permission_in_context

bill_detail_router = APIRouter()


@bill_detail_router.post(
    "/add",
    response_model=BillDetailResponseSchema,
    summary="Добавить деталь счета",
    status_code=status.HTTP_201_CREATED
)
async def add_bill_detail(
    data: BillDetailCreateSchema,
    context=Depends(require_permission_in_context("add_bill_detail"))
):
    bill = await Bills.get_or_none(bill_id=data.bill).prefetch_related("seller")
    service = await Service.get_or_none(service_id=data.service)

    if not bill or not service:
        raise HTTPException(
            status_code=400, detail="Счет или услуга не найдены")

    if not context.get("is_superadmin"):
        is_seller = await EntityCompanyRelation.exists(
            company_id=context["company"],
            legal_entity=bill.seller,
            relation_type="seller"
        )
        if not is_seller:
            raise HTTPException(
                status_code=403, detail="Нельзя добавлять детали к счету другой компании")
    try:
        bill_detail = await BillDetails.create(
            bill=bill,
            service=service,
            quantity=data.quantity,
            summ=data.quantity*data.price,
            price=data.price
        )
        return {"bill_detail_id": str(bill_detail.bill_detail_id)}

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


# --- Обновление существующей детали счета ---
@bill_detail_router.patch(
    "/{bill_detail_id}",
    response_model=BillDetailResponseSchema,
    summary="Изменить деталь счета"
)
async def update_bill_detail(
    bill_detail_id: UUID,
    data: BillDetailEditSchema,
    context=with_permission_through_bill("edit_bill_detail")
):
    bill_detail = await BillDetails.filter(bill_detail_id=bill_detail_id).first()
    if not bill_detail:
        raise HTTPException(status_code=404, detail="Деталь счета не найдена")

    update_data = data.dict(exclude_unset=True)

    await bill_detail.update_from_dict(update_data)
    # Пересчитываем сумму только если изменились price или quantity
    if "price" in update_data or "quantity" in update_data:
        bill_detail.summ = bill_detail.price * bill_detail.quantity

    await bill_detail.save()

    return {"bill_detail_id": str(bill_detail.bill_detail_id)}


# --- Удаление детали счета ---
@bill_detail_router.delete(
    "/{bill_detail_id}",
    summary="Удалить деталь счета",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_bill_detail(
    bill_detail_id: UUID,
    context=with_permission_through_bill("delete_bill_detail")
):
    bill_detail = await BillDetails.filter(bill_detail_id=bill_detail_id).first()
    if not bill_detail:
        raise HTTPException(status_code=404, detail="Деталь счета не найдена")

    await bill_detail.delete()


@bill_detail_router.get(
    "/all",
    response_model=BillDetailListResponseSchema,
    summary="Получение списка деталей счета"
)
async def get_bill_details(
        filters: dict = Depends(bill_detail_filter_params),
        context=Depends(require_permission_in_context("get_all_bill_details"))):
    try:
        query = Q()

        if not context.get("is_superadmin"):
            allowed_bill_ids = await Bills.filter(
                seller__entity_company_relations__company_id=context["company"],
                seller__entity_company_relations__relation_type="seller"
            ).values_list("bill_id", flat=True)

            query &= Q(bill_id__in=allowed_bill_ids)

        if filters.get("bill"):
            query &= Q(bill_id=filters["bill"])
        if filters.get("service"):
            query &= Q(service_id=filters["service"])
        if filters.get("bill"):
            query &= Q(bill_id=filters["bill"])
        if filters.get("service"):
            query &= Q(service_id=filters["service"])

        # ✅ Общее число записей
        total_count = await BillDetails.filter(query).count()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        bill_details = await BillDetails.filter(query) \
            .prefetch_related("bill", "service") \
            .offset((page - 1) * page_size) \
            .limit(page_size)

        return BillDetailListResponseSchema(
            total=total_count,
            bill_details=[
                BillDetailSchema(
                    bill_detail_id=bill_detail.bill_detail_id,
                    bill=bill_detail.bill.bill_id,
                    service=bill_detail.service.service_id,
                    quantity=bill_detail.quantity,
                    summ=bill_detail.summ,
                    price=bill_detail.price
                )
                for bill_detail in bill_details
            ]
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


# --- Получение одной детали счета по ID ---
@bill_detail_router.get(
    "/{bill_detail_id}",
    response_model=BillDetailSchema,
    summary="Просмотр одной детали счета"
)
async def get_bill_detail(
    bill_detail_id: UUID,
    context=with_permission_through_bill("view_bill_detail")
):
    bill_detail = await BillDetails.filter(bill_detail_id=bill_detail_id).prefetch_related("bill", "service").first()
    if not bill_detail:
        raise HTTPException(status_code=404, detail="Деталь счета не найдена")

    return BillDetailSchema(
        bill_detail_id=bill_detail.bill_detail_id,
        bill=bill_detail.bill.bill_id,
        service=bill_detail.service.service_id,
        quantity=bill_detail.quantity,
        summ=bill_detail.summ,
        price=bill_detail.price
    )
