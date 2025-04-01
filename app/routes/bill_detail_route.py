from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import BillDetails, Bills, Service
from app.pydantic_models.bill_detail_models import (
    BillDetailCreateSchema,
    BillDetailResponseSchema,
    BillDetailEditSchema,
    BillDetailSchema,
    bill_detail_filter_params,
    BillDetailListResponseSchema
)
from app.handlers.auth import get_current_user

bill_detail_router = APIRouter()


# --- Добавление новой детали счета ---
@bill_detail_router.post(
    "/add",
    response_model=BillDetailResponseSchema,
    summary="Добавить деталь счета",
    status_code=status.HTTP_201_CREATED
)
async def add_bill_detail(data: BillDetailCreateSchema, username: str = Depends(get_current_user)):
    try:
        bill = await Bills.get_or_none(bill_id=data.bill)
        service = await Service.get_or_none(service_id=data.service)

        if not bill or not service:
            raise HTTPException(
                status_code=400, detail="Счет или услуга не найдены"
            )

        bill_detail = await BillDetails.create(
            bill=bill,
            service=service,
            quantity=data.quantity,
            summ=data.summ
        )
        return {"bill_detail_id": str(bill_detail.bill_detail_id)}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при создании детали счета")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


# --- Обновление существующей детали счета ---
@bill_detail_router.patch(
    "/{bill_detail_id}",
    response_model=BillDetailResponseSchema,
    summary="Изменить деталь счета"
)
async def update_bill_detail(bill_detail_id: UUID, data: BillDetailEditSchema, username: str = Depends(get_current_user)):
    bill_detail = await BillDetails.filter(bill_detail_id=bill_detail_id).first()
    if not bill_detail:
        raise HTTPException(status_code=404, detail="Деталь счета не найдена")

    update_data = data.dict(exclude_unset=True)

    await bill_detail.update_from_dict(update_data)
    await bill_detail.save()

    return {"bill_detail_id": str(bill_detail.bill_detail_id)}


# --- Удаление детали счета ---
@bill_detail_router.delete(
    "/{bill_detail_id}",
    summary="Удалить деталь счета",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_bill_detail(bill_detail_id: UUID, username: str = Depends(get_current_user)):
    bill_detail = await BillDetails.filter(bill_detail_id=bill_detail_id).first()
    if not bill_detail:
        raise HTTPException(status_code=404, detail="Деталь счета не найдена")

    await bill_detail.delete()


@bill_detail_router.get(
    "/all",
    response_model=BillDetailListResponseSchema,
    summary="Получение списка деталей счета"
)
async def get_bill_details(filters: dict = Depends(bill_detail_filter_params), username: str = Depends(get_current_user)):
    try:
        query = Q()
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
                    bill=bill_detail.bill.bill_id,  # ✅ Теперь передаем ID счета
                    service=bill_detail.service.service_id,  # ✅ Теперь передаем ID услуги
                    quantity=bill_detail.quantity,
                    summ=bill_detail.summ
                )
                for bill_detail in bill_details
            ]
        )

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при получении списка деталей счета")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


# --- Получение одной детали счета по ID ---
@bill_detail_router.get(
    "/{bill_detail_id}",
    response_model=BillDetailSchema,
    summary="Просмотр одной детали счета"
)
async def get_bill_detail(bill_detail_id: UUID, username: str = Depends(get_current_user)):
    bill_detail = await BillDetails.filter(bill_detail_id=bill_detail_id).prefetch_related("bill", "service").first()
    if not bill_detail:
        raise HTTPException(status_code=404, detail="Деталь счета не найдена")

    return BillDetailSchema(
        bill_detail_id=bill_detail.bill_detail_id,
        bill=bill_detail.bill.bill_id,  # ✅ Передаем UUID счета
        service=bill_detail.service.service_id,  # ✅ Передаем UUID услуги
        quantity=bill_detail.quantity,
        summ=bill_detail.summ
    )
