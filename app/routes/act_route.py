from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import Acts, Contract
from app.pydantic_models.act_models import (
    ActCreateSchema,
    ActResponseSchema,
    ActEditSchema,
    act_filter_params,
    ActSchema
)


act_router = APIRouter()


@act_router.post(
    "/add",
    response_model=ActResponseSchema,
    summary="Добавить акт",
    status_code=status.HTTP_201_CREATED
)
async def add_act(data: ActCreateSchema):
    try:
        contract = await Contract.get_or_none(contract_id=data.contract)

        if not contract:
            raise HTTPException(status_code=400, detail="Контракт не найден")

        act = await Acts.create(
            act_number=data.act_number,
            act_date=data.act_date,
            contract=contract
        )
        return {"act_id": str(act.act_id)}

    except Exception as e:
        logger.exception("Ошибка при создании акта")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@act_router.patch(
    "/{act_id}",
    response_model=ActResponseSchema,
    summary="Изменить акт"
)
async def update_act(act_id: UUID, data: ActEditSchema):
    act = await Acts.filter(act_id=act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    update_data = data.dict(exclude_unset=True)

    if "contract" in update_data:
        contract = await Contract.get_or_none(contract_id=update_data["contract"])
        if not contract:
            raise HTTPException(status_code=400, detail="Контракт не найден")
        update_data["contract"] = contract

    await act.update_from_dict(update_data)
    await act.save()

    return {"act_id": str(act.act_id)}


@act_router.delete(
    "/{act_id}",
    summary="Удалить акт",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_act(act_id: UUID):
    act = await Acts.filter(act_id=act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    await act.delete()
    # return {"message": "Акт удалён"}


@act_router.get(
    "/all",
    response_model=List[ActSchema],
    summary="Получение списка актов"
)
async def get_acts(filters: dict = Depends(act_filter_params)):
    try:
        query = Q()
        if filters.get("contract"):
            query &= Q(contract_id=filters["contract"])

        acts = await Acts.filter(query) \
            .prefetch_related("contract") \
            .offset((filters["page"] - 1) * filters["page_size"]) \
            .limit(filters["page_size"])

        return [
            ActSchema(
                act_id=act.act_id,
                contract=act.contract.contract_id,  # ✅ Теперь передаем UUID
                act_number=act.act_number,
                act_date=act.act_date
            )
            for act in acts
        ]

    except Exception as e:
        logger.exception("Ошибка при получении списка актов")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@act_router.get(
    "/{act_id}",
    response_model=ActSchema,
    summary="Просмотр одного акта"
)
async def get_act(act_id: UUID):
    act = await Acts.filter(act_id=act_id).prefetch_related("contract").first()

    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    return ActSchema(
        act_id=act.act_id,
        contract=act.contract.contract_id,  # ✅ Теперь передаем UUID
        act_number=act.act_number,
        act_date=act.act_date
    )
