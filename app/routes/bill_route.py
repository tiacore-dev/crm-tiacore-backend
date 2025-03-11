from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import Bills, BankAccount, Contract
from app.pydantic_models.bill_models import (
    BillCreateSchema,
    BillResponseSchema,
    BillEditSchema,
    bill_filter_params,
    BillSchema
)


bill_router = APIRouter()


@bill_router.post(
    "/add",
    response_model=BillResponseSchema,
    summary="Добавить счет",
    status_code=status.HTTP_201_CREATED
)
async def add_bill(data: BillCreateSchema):
    try:
        bank_account = await BankAccount.get_or_none(bank_account_id=data.bank_account)
        contract = await Contract.get_or_none(contract_id=data.contract)

        if not bank_account or not contract:
            raise HTTPException(
                status_code=400, detail="Банковский счет или контракт не найдены"
            )

        bill = await Bills.create(
            bank_account=bank_account,
            bill_number=data.bill_number,
            bill_date=data.bill_date,
            contract=contract,
        )
        return {"bill_id": str(bill.bill_id)}

    except Exception as e:
        logger.exception("Ошибка при создании счета")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@bill_router.patch(
    "/{bill_id}",
    response_model=BillResponseSchema,
    summary="Изменить счет"
)
async def update_bill(bill_id: UUID, data: BillEditSchema):
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

    await bill.update_from_dict(update_data)
    await bill.save()

    return {"bill_id": str(bill.bill_id)}


@bill_router.delete(
    "/{bill_id}",
    summary="Удалить счет",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_bill(bill_id: UUID):
    bill = await Bills.filter(bill_id=bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Счет не найден")

    await bill.delete()
    # return {"message": "Счет удалён"}


@bill_router.get("/all", response_model=List[BillSchema], summary="Получение списка счетов")
async def get_bills(filters: dict = Depends(bill_filter_params)):
    try:
        query = Q()
        if filters.get("contract"):
            query &= Q(contract_id=filters["contract"])
        if filters.get("bank_account"):
            query &= Q(bank_account_id=filters["bank_account"])

        bills = await Bills.filter(query).prefetch_related("contract", "bank_account") \
            .offset((filters["page"] - 1) * filters["page_size"]).limit(filters["page_size"])

        return [
            BillSchema(
                bill_id=bill.bill_id,
                bill_number=bill.bill_number,
                bill_date=bill.bill_date,
                contract=bill.contract.contract_id,  # 👈 Теперь UUID передается явно
                bank_account=bill.bank_account.bank_account_id  # 👈 Теперь UUID передается явно
            )
            for bill in bills
        ]

    except Exception as e:
        logger.exception("Ошибка при получении списка счетов")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@bill_router.get(
    "/{bill_id}",
    response_model=BillSchema,
    summary="Просмотр одного счета"
)
async def get_bill(bill_id: UUID):
    bill = await Bills.filter(bill_id=bill_id).prefetch_related("contract", "bank_account").first()
    if not bill:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return BillSchema(
        bill_id=bill.bill_id,
        bill_number=bill.bill_number,
        bill_date=bill.bill_date,
        contract=bill.contract.contract_id,  # 👈 Передаем UUID контракта
        bank_account=bill.bank_account.bank_account_id,  # 👈 Передаем UUID счета
    )
