from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import Contract, ContractStatus, LegalEntity
from app.pydantic_models.contract_models import (
    ContractCreateSchema,
    ContractResponseSchema,
    ContractEditSchema,
    contract_filter_params,
    ContractSchema,
    ContractListResponseSchema
)
from app.handlers.auth import get_current_user
from app.s3.s3_manager import AsyncS3Manager

contract_router = APIRouter()


@contract_router.post(
    "/add",
    response_model=ContractResponseSchema,
    summary="Добавить контракт",
    status_code=status.HTTP_201_CREATED
)
async def add_contract(data: ContractCreateSchema = Depends(ContractCreateSchema.as_form), username: str = Depends(get_current_user)):
    try:
        buyer = await LegalEntity.get_or_none(legal_entity_id=data.buyer)
        seller = await LegalEntity.get_or_none(legal_entity_id=data.seller)
        status_obj = await ContractStatus.get_or_none(contract_status_id=data.status)

        if not buyer or not seller or not status_obj:
            raise HTTPException(
                status_code=400, detail="Покупатель, продавец или статус не найдены"
            )
        s3_key = None
        if data.file:

            file_bytes = await data.file.read()
            if not file_bytes:
                raise HTTPException(
                    status_code=400, detail="Не удалось загрузить данные файла"
                )

            logger.info(
                f"Тип загружаемых данных: {type(file_bytes)}, размер: {len(file_bytes)} байт")

            filename = data.file.filename
            manager = AsyncS3Manager()
            s3_key = await manager.upload_bytes(file_bytes, f"{data.buyer}+{data.seller}", filename, entity="contract")

        contract = await Contract.create(
            contract_name=data.contract_name,
            contract_date=data.contract_date,
            buyer=buyer,
            seller=seller,
            comment=data.comment,
            s3_key=s3_key,
            status=status_obj,
        )
        return {"contract_id": str(contract.contract_id)}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при создании контракта")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@contract_router.patch(
    "/{contract_id}",
    response_model=ContractResponseSchema,
    summary="Изменить контракт"
)
async def update_contract(contract_id: UUID, data: ContractEditSchema = Depends(ContractEditSchema.as_form), username: str = Depends(get_current_user)):
    contract = await Contract.filter(contract_id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    update_data = {}

    if data.buyer:
        buyer = await LegalEntity.get_or_none(legal_entity_id=data.buyer)
        if not buyer:
            raise HTTPException(status_code=400, detail="Покупатель не найден")
        update_data["buyer"] = buyer

    if data.seller:
        seller = await LegalEntity.get_or_none(legal_entity_id=data.seller)
        if not seller:
            raise HTTPException(status_code=400, detail="Продавец не найден")
        update_data["seller"] = seller

    if data.status:
        status_obj = await ContractStatus.get_or_none(contract_status_id=data.status)
        if not status_obj:
            raise HTTPException(status_code=400, detail="Статус не найден")
        update_data["status"] = status_obj

    if data.file:
        manager = AsyncS3Manager()
        file_bytes = await data.file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=400, detail="Не удалось загрузить файл")

        # Удаляем старый файл
        await manager.delete_file(contract.s3_key)

        # Загружаем новый
        new_s3_key = await manager.upload_bytes(file_bytes, f"{data.buyer}+{data.seller}", data.file.filename, entity="contract")
        update_data["s3_key"] = new_s3_key

    if data.contract_name:
        update_data['contract_name'] = data.contract_name
    if data.contract_date:
        update_data['contract_date'] = data.contract_date
    if data.comment:
        update_data['comment'] = data.comment

    await contract.update_from_dict(update_data)
    await contract.save()

    return {"contract_id": str(contract.contract_id)}


@contract_router.delete(
    "/{contract_id}",
    summary="Удалить контракт",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contract(contract_id: UUID, username: str = Depends(get_current_user)):
    contract = await Contract.filter(contract_id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    await contract.delete()
    # return {"message": "Контракт удалён"}


@contract_router.get(
    "/all",
    response_model=ContractListResponseSchema,
    summary="Получение списка контрактов"
)
async def get_contracts(filters: dict = Depends(contract_filter_params), username: str = Depends(get_current_user)):
    try:
        query = Q()
        if filters.get("buyer"):
            query &= Q(buyer_id=filters["buyer"])
        if filters.get("seller"):
            query &= Q(seller_id=filters["seller"])
        if filters.get("status"):
            query &= Q(status_id=filters["status"])

        # ✅ Общее число записей
        total_count = await Contract.filter(query).count()

        contracts = await Contract.filter(query) \
            .prefetch_related("buyer", "seller", "status") \
            .offset((filters["page"] - 1) * filters["page_size"]) \
            .limit(filters["page_size"])

        return ContractListResponseSchema(
            total=total_count,
            contracts=[
                ContractSchema(
                    contract_id=contract.contract_id,
                    contract_name=contract.contract_name,
                    contract_date=contract.contract_date,
                    buyer=contract.buyer.legal_entity_id,  # Теперь ID
                    seller=contract.seller.legal_entity_id,  # Теперь ID
                    status=contract.status.contract_status_id,  # Теперь ID
                    s3_key=contract.s3_key,
                    comment=contract.comment
                )
                for contract in contracts
            ]
        )

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при получении списка контрактов")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@contract_router.get(
    "/{contract_id}",
    response_model=ContractSchema,
    summary="Просмотр одного контракта"
)
async def get_contract(contract_id: UUID, username: str = Depends(get_current_user)):
    contract = await Contract.filter(contract_id=contract_id).prefetch_related("buyer", "seller", "status").first()

    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    return ContractSchema(
        contract_id=contract.contract_id,
        contract_name=contract.contract_name,
        contract_date=contract.contract_date,
        buyer=contract.buyer.legal_entity_id,
        seller=contract.seller.legal_entity_id,
        status=contract.status.contract_status_id,
        s3_key=contract.s3_key,
        comment=contract.comment
    )
