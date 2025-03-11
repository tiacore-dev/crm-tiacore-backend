from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from tortoise.contrib.pydantic import pydantic_model_creator
from loguru import logger
from app.database.models import BankAccount, LegalEntity
from app.pydantic_models.bank_account_models import (
    BankAccountCreateSchema,
    BankAccountResponseSchema,
    BankAccountEditSchema,
    bank_account_filter_params
)

BankAccountSchema = pydantic_model_creator(
    BankAccount, name="BankAccountSchema")

bank_account_router = APIRouter()


@bank_account_router.post(
    "/add",
    response_model=BankAccountResponseSchema,
    summary="Добавить банковский счет",
    status_code=status.HTTP_201_CREATED
)
async def add_bank_account(data: BankAccountCreateSchema):
    try:
        legal_entity = await LegalEntity.get_or_none(legal_entity_id=data.legal_entity)

        if not legal_entity:
            raise HTTPException(
                status_code=400, detail="Юридическое лицо не найдено")

        bank_account = await BankAccount.create(
            account_number=data.account_number,
            bank_name=data.bank_name,
            bank_bic=data.bank_bic,
            bank_corr_account=data.bank_corr_account,
            legal_entity=legal_entity,
        )
        return {"bank_account_id": str(bank_account.bank_account_id)}

    except Exception as e:
        logger.exception("Ошибка при создании банковского счета")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@bank_account_router.patch(
    "/{bank_account_id}",
    response_model=BankAccountResponseSchema,
    summary="Изменить банковский счет"
)
async def update_bank_account(bank_account_id: UUID, data: BankAccountEditSchema):
    bank_account = await BankAccount.filter(bank_account_id=bank_account_id).first()
    if not bank_account:
        raise HTTPException(
            status_code=404, detail="Банковский счет не найден")

    update_data = data.dict(exclude_unset=True)

    if "legal_entity" in update_data:
        legal_entity = await LegalEntity.get_or_none(legal_entity_id=update_data["legal_entity"])
        if not legal_entity:
            raise HTTPException(
                status_code=400, detail="Юридическое лицо не найдено")
        update_data["legal_entity"] = legal_entity

    await bank_account.update_from_dict(update_data)
    await bank_account.save()

    return {"bank_account_id": str(bank_account.bank_account_id)}


@bank_account_router.delete(
    "/{bank_account_id}",
    summary="Удалить банковский счет",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_bank_account(bank_account_id: UUID):
    bank_account = await BankAccount.filter(bank_account_id=bank_account_id).first()
    if not bank_account:
        raise HTTPException(
            status_code=404, detail="Банковский счет не найден")

    await bank_account.delete()
    # return {"message": "Банковский счет удалён"}


@bank_account_router.get(
    "/all",
    response_model=List[BankAccountSchema],
    summary="Получение списка банковских счетов"
)
async def get_bank_accounts(filters: dict = Depends(bank_account_filter_params)):
    try:
        query = Q()
        if filters.get("legal_entity"):
            query &= Q(legal_entity_id=filters["legal_entity"])
        if filters.get("bank_name"):
            query &= Q(bank_name__icontains=filters["bank_name"])

        bank_accounts = await BankAccount.filter(query).offset((filters["page"] - 1) * filters["page_size"]).limit(filters["page_size"])
        return [await BankAccountSchema.from_tortoise_orm(bank_account) for bank_account in bank_accounts]

    except Exception as e:
        logger.exception("Ошибка при получении списка банковских счетов")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@bank_account_router.get(
    "/{bank_account_id}",
    response_model=BankAccountSchema,
    summary="Просмотр одного банковского счета"
)
async def get_bank_account(bank_account_id: UUID):
    bank_account = await BankAccount.filter(bank_account_id=bank_account_id).first()
    if not bank_account:
        raise HTTPException(
            status_code=404, detail="Банковский счет не найден")
    return await BankAccountSchema.from_tortoise_orm(bank_account)
