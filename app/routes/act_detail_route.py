from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from tortoise.contrib.pydantic import pydantic_model_creator
from loguru import logger
from app.database.models import ActDetails, Acts, Service
from app.pydantic_models.act_detail_models import (
    ActDetailCreateSchema,
    ActDetailResponseSchema,
    ActDetailEditSchema,
    act_detail_filter_params
)

ActDetailSchema = pydantic_model_creator(ActDetails, name="ActDetailSchema")

act_detail_router = APIRouter()


@act_detail_router.post(
    "/add",
    response_model=ActDetailResponseSchema,
    summary="Добавить детали акта",
    status_code=status.HTTP_201_CREATED
)
async def add_act_detail(data: ActDetailCreateSchema):
    try:
        act = await Acts.get_or_none(act_id=data.act)
        service = await Service.get_or_none(service_id=data.service)

        if not act or not service:
            raise HTTPException(
                status_code=400, detail="Акт или услуга не найдены"
            )

        act_detail = await ActDetails.create(
            act=act,
            service=service,
            quantity=data.quantity,
            summ=data.summ
        )
        return {"act_detail_id": str(act_detail.act_detail_id)}

    except Exception as e:
        logger.exception("Ошибка при создании детали акта")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@act_detail_router.patch(
    "/{act_detail_id}",
    response_model=ActDetailResponseSchema,
    summary="Изменить детали акта"
)
async def update_act_detail(act_detail_id: UUID, data: ActDetailEditSchema):
    act_detail = await ActDetails.filter(act_detail_id=act_detail_id).first()
    if not act_detail:
        raise HTTPException(status_code=404, detail="Деталь акта не найдена")

    update_data = data.dict(exclude_unset=True)

    if "act" in update_data:
        act = await Acts.get_or_none(act_id=update_data["act"])
        if not act:
            raise HTTPException(status_code=400, detail="Акт не найден")
        update_data["act"] = act

    if "service" in update_data:
        service = await Service.get_or_none(service_id=update_data["service"])
        if not service:
            raise HTTPException(status_code=400, detail="Услуга не найдена")
        update_data["service"] = service

    await act_detail.update_from_dict(update_data)
    await act_detail.save()

    return {"act_detail_id": str(act_detail.act_detail_id)}


@act_detail_router.delete(
    "/{act_detail_id}",
    summary="Удалить детали акта",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_act_detail(act_detail_id: UUID):
    act_detail = await ActDetails.filter(act_detail_id=act_detail_id).first()
    if not act_detail:
        raise HTTPException(status_code=404, detail="Деталь акта не найдена")

    await act_detail.delete()
    # return {"message": "Деталь акта удалена"}


@act_detail_router.get(
    "/all",
    response_model=List[ActDetailSchema],
    summary="Получение списка деталей акта"
)
async def get_act_details(filters: dict = Depends(act_detail_filter_params)):
    try:
        query = Q()
        if filters.get("act"):
            query &= Q(act_id=filters["act"])
        if filters.get("service"):
            query &= Q(service_id=filters["service"])

        act_details = await ActDetails.filter(query) \
            .prefetch_related("act", "service") \
            .offset((filters["page"] - 1) * filters["page_size"]) \
            .limit(filters["page_size"])

        return [await ActDetailSchema.from_tortoise_orm(act_detail) for act_detail in act_details]

    except Exception as e:
        logger.exception("Ошибка при получении списка деталей акта")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@act_detail_router.get(
    "/{act_detail_id}",
    response_model=ActDetailSchema,
    summary="Просмотр одной детали акта"
)
async def get_act_detail(act_detail_id: UUID):
    act_detail = await ActDetails.filter(act_detail_id=act_detail_id).prefetch_related("act", "service").first()

    if not act_detail:
        raise HTTPException(status_code=404, detail="Деталь акта не найдена")

    return await ActDetailSchema.from_tortoise_orm(act_detail)
