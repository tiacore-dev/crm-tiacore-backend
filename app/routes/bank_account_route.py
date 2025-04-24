from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import BankAccount, LegalEntity, EntityCompanyRelation
from app.pydantic_models.bank_account_models import (
    BankAccountCreateSchema,
    BankAccountResponseSchema,
    BankAccountEditSchema,
    bank_account_filter_params,
    BankAccountSchema,
    BankAccountListResponseSchema
)
from app.handlers.depends import require_permission_in_context
from app.dependencies.permissions import with_permission_and_entity_company_check_for_bank
from app.utils.permissions_get import ensure_seller_belongs_to_company


bank_account_router = APIRouter()


@bank_account_router.post(
    "/add",
    response_model=BankAccountResponseSchema,
    summary="Добавить банковский счет",
    status_code=status.HTTP_201_CREATED
)
async def add_bank_account(
        data: BankAccountCreateSchema,
        context=Depends(require_permission_in_context("add_act"))):
    try:
        legal_entity = await LegalEntity.get_or_none(legal_entity_id=data.legal_entity)

        if not legal_entity:
            raise HTTPException(
                status_code=400, detail="Юридическое лицо не найдено")

        if not context.get("is_superadmin"):
            await ensure_seller_belongs_to_company(legal_entity, context["company"])

        bank_account = await BankAccount.create(
            account_number=data.account_number,
            bank_name=data.bank_name,
            bank_bic=data.bank_bic,
            bank_corr_account=data.bank_corr_account,
            legal_entity=legal_entity,
        )
        return {"bank_account_id": str(bank_account.bank_account_id)}

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@bank_account_router.patch(
    "/{bank_account_id}",
    response_model=BankAccountResponseSchema,
    summary="Изменить банковский счет"
)
async def update_bank_account(
        bank_account_id: UUID,
        data: BankAccountEditSchema,
        context=with_permission_and_entity_company_check_for_bank("edit_bank_account")):
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
async def delete_bank_account(
    bank_account_id: UUID,
    context=with_permission_and_entity_company_check_for_bank(
        "delete_bank_account")
):
    bank_account = await BankAccount.filter(bank_account_id=bank_account_id).first()
    if not bank_account:
        raise HTTPException(
            status_code=404, detail="Банковский счет не найден")

    await bank_account.delete()
    # return {"message": "Банковский счет удалён"}


@bank_account_router.get(
    "/all",
    response_model=BankAccountListResponseSchema,
    summary="Получение списка банковских счетов"
)
async def get_bank_accounts(
        filters: dict = Depends(bank_account_filter_params),
        context=Depends(require_permission_in_context("get_all_bank_accounts"))
):
    try:
        query = Q()
        if not context.get("is_superadmin"):
            related_entity_ids = await EntityCompanyRelation.filter(
                company_id=context["company"],
                relation_type="seller"
            ).values_list("legal_entity_id", flat=True)
            query &= Q(legal_entity_id__in=related_entity_ids)
        else:
            if filters.get("legal_entity"):
                query &= Q(legal_entity_id=filters["legal_entity"])
        if filters.get("bank_name"):
            query &= Q(bank_name__icontains=filters["bank_name"])

        # ✅ Общее число записей
        total_count = await BankAccount.filter(query).count()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        bank_accounts = await BankAccount.filter(query) \
            .prefetch_related("legal_entity") \
            .offset((page - 1) * page_size) \
            .limit(page_size)

        return BankAccountListResponseSchema(
            total=total_count,
            bank_accounts=[
                BankAccountSchema(
                    bank_account_id=bank_account.bank_account_id,
                    # ✅ Теперь передаем UUID юр. лица
                    legal_entity=bank_account.legal_entity.legal_entity_id,
                    bank_name=bank_account.bank_name,
                    account_number=bank_account.account_number,
                    bank_bic=bank_account.bank_bic,
                    bank_corr_account=bank_account.bank_corr_account
                )
                for bank_account in bank_accounts
            ]
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@bank_account_router.get(
    "/{bank_account_id}",
    response_model=BankAccountSchema,
    summary="Просмотр одного банковского счета"
)
async def get_bank_account(
    bank_account_id: UUID,
    context=with_permission_and_entity_company_check_for_bank(
        "view_bank_account")
):
    bank_account = await BankAccount.filter(bank_account_id=bank_account_id).prefetch_related("legal_entity").first()

    if not bank_account:
        raise HTTPException(
            status_code=404, detail="Банковский счет не найден"
        )

    return BankAccountSchema(
        bank_account_id=bank_account.bank_account_id,
        legal_entity=bank_account.legal_entity.legal_entity_id,  # ✅ Теперь передаем UUID
        bank_name=bank_account.bank_name,
        account_number=bank_account.account_number,
        bank_bic=bank_account.bank_bic,
        bank_corr_account=bank_account.bank_corr_account
    )
