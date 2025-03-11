from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from tortoise.contrib.pydantic import pydantic_model_creator
from loguru import logger
from app.database.models import Contract, ContractStatus, LegalEntity
from app.pydantic_models.contract_models import (
    ContractCreateSchema,
    ContractResponseSchema,
    ContractEditSchema,
    contract_filter_params
)

ContractSchema = pydantic_model_creator(Contract, name="ContractSchema")

contract_router = APIRouter()


@contract_router.post(
    "/add",
    response_model=ContractResponseSchema,
    summary="Добавить контракт",
    status_code=status.HTTP_201_CREATED
)
async def add_contract(data: ContractCreateSchema):
    try:
        buyer = await LegalEntity.get_or_none(legal_entity_id=data.buyer)
        seller = await LegalEntity.get_or_none(legal_entity_id=data.seller)
        status_obj = await ContractStatus.get_or_none(contract_status_id=data.status)

        if not buyer or not seller or not status_obj:
            raise HTTPException(
                status_code=400, detail="Покупатель, продавец или статус не найдены"
            )

        contract = await Contract.create(
            contract_name=data.contract_name,
            contract_date=data.contract_date,
            buyer=buyer,
            seller=seller,
            comment=data.comment,
            file=data.file,
            status=status_obj,
        )
        return {"contract_id": str(contract.contract_id)}

    except Exception as e:
        logger.exception("Ошибка при создании контракта")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@contract_router.patch(
    "/{contract_id}",
    response_model=ContractResponseSchema,
    summary="Изменить контракт"
)
async def update_contract(contract_id: UUID, data: ContractEditSchema):
    contract = await Contract.filter(contract_id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    update_data = data.dict(exclude_unset=True)

    if "buyer" in update_data:
        buyer = await LegalEntity.get_or_none(legal_entity_id=update_data["buyer"])
        if not buyer:
            raise HTTPException(status_code=400, detail="Покупатель не найден")
        update_data["buyer"] = buyer

    if "seller" in update_data:
        seller = await LegalEntity.get_or_none(legal_entity_id=update_data["seller"])
        if not seller:
            raise HTTPException(status_code=400, detail="Продавец не найден")
        update_data["seller"] = seller

    if "status" in update_data:
        status_obj = await ContractStatus.get_or_none(contract_status_id=update_data["status"])
        if not status_obj:
            raise HTTPException(status_code=400, detail="Статус не найден")
        update_data["status"] = status_obj

    await contract.update_from_dict(update_data)
    await contract.save()

    return {"contract_id": str(contract.contract_id)}


@contract_router.delete(
    "/{contract_id}",
    summary="Удалить контракт",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contract(contract_id: UUID):
    contract = await Contract.filter(contract_id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    await contract.delete()
    # return {"message": "Контракт удалён"}


@contract_router.get(
    "/all",
    response_model=List[ContractSchema],
    summary="Получение списка контрактов"
)
async def get_contracts(filters: dict = Depends(contract_filter_params)):
    try:
        query = Q()
        if filters.get("buyer"):
            query &= Q(buyer_id=filters["buyer"])
        if filters.get("seller"):
            query &= Q(seller_id=filters["seller"])
        if filters.get("status"):
            query &= Q(status_id=filters["status"])

        contracts = await Contract.filter(query).offset((filters["page"] - 1) * filters["page_size"]).limit(filters["page_size"])
        return [await ContractSchema.from_tortoise_orm(contract) for contract in contracts]

    except Exception as e:
        logger.exception("Ошибка при получении списка контрактов")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@contract_router.get(
    "/{contract_id}",
    response_model=ContractSchema,
    summary="Просмотр одного контракта"
)
async def get_contract(contract_id: UUID):
    contract = await Contract.filter(contract_id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")
    return await ContractSchema.from_tortoise_orm(contract)
