from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tortoise.expressions import Q

from app.database.models import BankAccount, EntityCompanyRelation
from app.dependencies.permissions import (
    with_permission_and_entity_company_check_for_bank,
)
from app.pydantic_models.bank_account_models import (
    BankAccountCreateSchema,
    BankAccountEditSchema,
    BankAccountListResponseSchema,
    BankAccountResponseSchema,
    BankAccountSchema,
    bank_account_filter_params,
)
from app.utils.permissions_get import ensure_seller_belongs_to_company

bank_account_router = APIRouter()


@bank_account_router.post(
    "/add",
    response_model=BankAccountResponseSchema,
    summary="Добавить банковский счет",
    status_code=status.HTTP_201_CREATED,
)
async def add_bank_account(
    data: BankAccountCreateSchema,
    context=Depends(require_permission_in_context("add_act")),
):
    if not context.get("is_superadmin"):
        await ensure_seller_belongs_to_company(
            data.legal_entity_id, context["company_id"]
        )

    bank_account = await BankAccount.create(**data.model_dump())
    return BankAccountResponseSchema(bank_account_id=bank_account.id)


@bank_account_router.patch(
    "/{bank_account_id}",
    response_model=BankAccountResponseSchema,
    summary="Изменить банковский счет",
)
async def update_bank_account(
    bank_account_id: UUID,
    data: BankAccountEditSchema,
    _=with_permission_and_entity_company_check_for_bank("edit_bank_account"),
):
    bank_account = await BankAccount.filter(id=bank_account_id).first()
    if not bank_account:
        raise HTTPException(status_code=404, detail="Банковский счет не найден")

    update_data = data.model_dump(exclude_unset=True)

    await bank_account.update_from_dict(update_data)
    await bank_account.save()

    return BankAccountResponseSchema(bank_account_id=bank_account.id)


@bank_account_router.delete(
    "/{bank_account_id}",
    summary="Удалить банковский счет",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_bank_account(
    bank_account_id: UUID,
    _=with_permission_and_entity_company_check_for_bank("delete_bank_account"),
):
    bank_account = await BankAccount.filter(id=bank_account_id).first()
    if not bank_account:
        raise HTTPException(status_code=404, detail="Банковский счет не найден")

    await bank_account.delete()
    return


@bank_account_router.get(
    "/all",
    response_model=BankAccountListResponseSchema,
    summary="Получение списка банковских счетов",
)
async def get_bank_accounts(
    filters: dict = Depends(bank_account_filter_params),
    context=Depends(require_permission_in_context("get_all_bank_accounts")),
):
    try:
        query = Q()
        if not context.get("is_superadmin"):
            related_entity_ids = await EntityCompanyRelation.filter(
                company_id=context["company_id"], relation_type="seller"
            ).values_list("legal_entity_id", flat=True)

            # ✅ если фильтр legal_entity есть — проверим, входит ли он в разрешённые
            if filters.get("legal_entity"):
                legal_entity = filters["legal_entity"]
                if legal_entity in related_entity_ids:
                    query &= Q(legal_entity_id=legal_entity)
                else:
                    # Нет доступа к указанному юрлицу
                    return BankAccountListResponseSchema(total=0, bank_accounts=[])
            else:
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

        bank_accounts = (
            await BankAccount.filter(query)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return BankAccountListResponseSchema(
            total=total_count,
            bank_accounts=[
                BankAccountSchema(
                    bank_account_id=bank_account.id,
                    legal_entity=bank_account.legal_entity_id,
                    bank_name=bank_account.bank_name,
                    account_number=bank_account.number,
                    bank_bic=bank_account.bank_bic,
                    bank_corr_account=bank_account.bank_corr_account,
                )
                for bank_account in bank_accounts
            ],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@bank_account_router.get(
    "/{bank_account_id}",
    response_model=BankAccountSchema,
    summary="Просмотр одного банковского счета",
)
async def get_bank_account(
    bank_account_id: UUID,
    _=with_permission_and_entity_company_check_for_bank("view_bank_account"),
):
    bank_account = await BankAccount.filter(id=bank_account_id).first()

    if not bank_account:
        raise HTTPException(status_code=404, detail="Банковский счет не найден")

    return BankAccountSchema(
        bank_account_id=bank_account.id,
        legal_entity=bank_account_id,
        bank_name=bank_account.bank_name,
        account_number=bank_account.number,
        bank_bic=bank_account.bank_bic,
        bank_corr_account=bank_account.bank_corr_account,
    )
