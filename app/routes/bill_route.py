from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import Bills, BankAccount, Contract, LegalEntity
from app.pydantic_models.bill_models import (
    BillCreateSchema,
    BillResponseSchema,
    BillEditSchema,
    bill_filter_params,
    BillSchema,
    BillListResponseSchema
)
from app.handlers.auth import get_current_user


bill_router = APIRouter()


@bill_router.post(
    "/add",
    response_model=BillResponseSchema,
    summary="Добавить счет",
    status_code=status.HTTP_201_CREATED
)
async def add_bill(data: BillCreateSchema, username: str = Depends(get_current_user)):
    try:
        bank_account = await BankAccount.get_or_none(bank_account_id=data.bank_account)
        if not bank_account:
            raise HTTPException(
                status_code=400, detail="Банковский счет  не найден"
            )
        contract = None
        if data.contract:
            contract = await Contract.get_or_none(contract_id=data.contract).prefetch_related("buyer", "seller")

            if not contract:
                raise HTTPException(
                    status_code=400, detail="Контракт не найден")

            data.buyer = contract.buyer.legal_entity_id
            data.seller = contract.seller.legal_entity_id
        buyer = await LegalEntity.get_or_none(legal_entity_id=data.buyer)
        seller = await LegalEntity.get_or_none(legal_entity_id=data.seller)
        if not buyer or not seller:
            raise HTTPException(
                status_code=400, detail="Юр. лица не найдены")

        bill = await Bills.create(
            bank_account=bank_account,
            bill_number=data.bill_number,
            bill_date=data.bill_date,
            contract=contract,
            buyer=buyer,
            seller=seller
        )
        return {"bill_id": str(bill.bill_id)}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при создании счета")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@bill_router.patch(
    "/{bill_id}",
    response_model=BillResponseSchema,
    summary="Изменить счет"
)
async def update_bill(bill_id: UUID, data: BillEditSchema, username: str = Depends(get_current_user)):
    bill = await Bills.filter(bill_id=bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Счет не найден")

    update_data = data.dict(exclude_unset=True)

    if "bank_account" in update_data:
        bank_account = await BankAccount.get_or_none(bank_account_id=update_data["bank_account"])
        if not bank_account:
            raise HTTPException(
                status_code=400, detail="Банковский счет не найден")
        update_data["bank_account"] = bank_account

    if "contract" in update_data:
        contract = await Contract.get_or_none(contract_id=update_data["contract"])
        if not contract:
            raise HTTPException(status_code=400, detail="Контракт не найден")
        update_data["contract"] = contract

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

    await bill.update_from_dict(update_data)
    await bill.save()

    return {"bill_id": str(bill.bill_id)}


@bill_router.delete(
    "/{bill_id}",
    summary="Удалить счет",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_bill(bill_id: UUID, username: str = Depends(get_current_user)):
    bill = await Bills.filter(bill_id=bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Счет не найден")

    await bill.delete()
    # return {"message": "Счет удалён"}


@bill_router.get(
    "/all",
    response_model=BillListResponseSchema,
    summary="Получение списка счетов"
)
async def get_bills(filters: dict = Depends(bill_filter_params), username: str = Depends(get_current_user)):
    try:
        query = Q()
        if filters.get("contract"):
            query &= Q(contract_id=filters["contract"])
        if filters.get("bank_account"):
            query &= Q(bank_account_id=filters["bank_account"])

        # ✅ Общее число записей
        total_count = await Bills.filter(query).count()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        bills = await Bills.filter(query) \
            .prefetch_related("contract", "bank_account", "buyer", "seller") \
            .offset((page - 1) * page_size) \
            .limit(page_size)

        return BillListResponseSchema(
            total=total_count,
            bills=[
                BillSchema(
                    bill_id=bill.bill_id,
                    bill_number=bill.bill_number,
                    bill_date=bill.bill_date,
                    contract=bill.contract.contract_id,
                    bank_account=bill.bank_account.bank_account_id,
                    buyer=bill.buyer.legal_entity_id,
                    seller=bill.seller.legal_entity_id
                )
                for bill in bills
            ]
        )

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при получении списка счетов")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@bill_router.get(
    "/{bill_id}",
    response_model=BillSchema,
    summary="Просмотр одного счета"
)
async def get_bill(bill_id: UUID, username: str = Depends(get_current_user)):
    bill = await Bills.filter(bill_id=bill_id).prefetch_related("contract", "bank_account", "buyer", "seller").first()
    if not bill:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return BillSchema(
        bill_id=bill.bill_id,
        bill_number=bill.bill_number,
        bill_date=bill.bill_date,
        contract=bill.contract.contract_id,
        bank_account=bill.bank_account.bank_account_id,
        buyer=bill.buyer.legal_entity_id,
        seller=bill.seller.legal_entity_id
    )
