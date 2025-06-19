from typing import Any, Callable, Type, cast
from uuid import UUID

from fastapi import Depends, HTTPException, Path
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tortoise.models import Model

from app.database.models import (
    ActDetails,
    Acts,
    BankAccount,
    BillDetails,
    Bills,
    Contract,
    EntityCompanyRelation,
    Service,
    Templates,
)


async def context_maker(
    context: dict,
    model: Type[Model],
    model_name: str,
    model_id: UUID,
    company_id_getter: Callable[[Model], UUID],
):
    instance = (
        await model.filter(**{f"{model_name}_id": model_id})
        .prefetch_related("company")
        .first()
    )
    if not instance:
        raise HTTPException(
            status_code=404, detail=f"{model_name.capitalize()} не найден"
        )

    if company_id_getter(instance) != context["company_id"]:
        raise HTTPException(
            status_code=403, detail="Вы не можете управлять этим объектом"
        )

    return context


def with_permission_and_seller_contract_check(permission: str):
    async def dependency(
        contract_id: UUID = Path(..., description="ID контракта"),
        context: dict = Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context
        return await context_maker(
            context,
            Contract,
            "contract",
            contract_id,
            lambda x: cast(Any, x).company.company_id,
        )

    return Depends(dependency)


def with_permission_and_seller_act_check(permission: str):
    async def dependency(
        act_id: UUID = Path(..., description="ID акта"),
        context: dict = Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context
        return await context_maker(
            context,
            Acts,
            "act",
            act_id,
            lambda x: cast(Any, x).company_id,
        )

    return Depends(dependency)


def with_permission_and_seller_bill_check(permission: str):
    async def dependency(
        bill_id: UUID = Path(..., description="ID счёта"),
        context: dict = Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context
        return await context_maker(
            context,
            Bills,
            "bill",
            bill_id,
            lambda x: cast(Any, x).company_id,
        )

    return Depends(dependency)


def with_permission_through_act(permission: str):
    async def dependency(
        act_detail_id: UUID = Path(...),
        context=Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context

        detail = await ActDetails.get_or_none(
            act_detail_id=act_detail_id
        ).prefetch_related("act__seller")
        if not detail:
            raise HTTPException(status_code=404, detail="Деталь акта не найдена")

        is_seller = await EntityCompanyRelation.exists(
            company_id=context["company_id"],
            legal_entity=detail.act.seller,
            relation_type="seller",
        )

        if not is_seller:
            raise HTTPException(
                status_code=403,
                detail="Вы не можете работать с деталями акта чужой компании",
            )

        return context

    return Depends(dependency)


def with_permission_through_bill(permission: str):
    async def dependency(
        bill_detail_id: UUID = Path(...),
        context=Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context

        detail = await BillDetails.get_or_none(
            bill_detail_id=bill_detail_id
        ).prefetch_related("bill__seller")
        if not detail:
            raise HTTPException(status_code=404, detail="Деталь акта не найдена")

        is_seller = await EntityCompanyRelation.exists(
            company_id=context["company_id"],
            legal_entity=detail.bill.seller,
            relation_type="seller",
        )

        if not is_seller:
            raise HTTPException(
                status_code=403,
                detail="Вы не можете работать с деталями акта чужой компании",
            )

        return context

    return Depends(dependency)


def with_permission_and_service_check(permission: str):
    async def dependency(
        service_id: UUID = Path(..., description="ID услуги"),
        context: dict = Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context

        # Проверка принадлежности услуги компании
        service = await Service.get_or_none(service_id=service_id).prefetch_related(
            "company"
        )

        if not service or str(service.company_id) != str(context["company_id"]):
            raise HTTPException(
                status_code=403,
                detail="Услуга не принадлежит указанной компании или не найдена",
            )

        return context

    return Depends(dependency)


def with_permission_and_entity_company_check_for_bank(
    permission: str,
):
    async def dependency(
        bank_account_id: UUID = Path(...),
        context: dict = Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context

        account = await BankAccount.get_or_none(
            bank_account_id=bank_account_id
        ).prefetch_related("legal_entity")
        if not account:
            raise HTTPException(
                status_code=404, detail=f"BankAccount {bank_account_id} не найден"
            )

        is_seller = await EntityCompanyRelation.exists(
            company_id=context["company_id"],
            legal_entity=account.legal_entity_id,
            relation_type="seller",
        )

        if not is_seller:
            raise HTTPException(
                status_code=403,
                detail="Вы не можете управлять банковским счетом с чужим продавцом",
            )

        return context

    return Depends(dependency)


def with_permission_and_template_check(permission: str):
    async def dependency(
        template_id: UUID = Path(..., description="ID услуги"),
        context: dict = Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context

        # Проверка принадлежности услуги компании
        template = await Templates.get_or_none(
            template_id=template_id
        ).prefetch_related("company")

        if not template:
            raise HTTPException(
                status_code=403,
                detail="Услуга не найдена",
            )
        if template.company_id:
            if str(template.company_id) != str(context["company_id"]):
                raise HTTPException(
                    status_code=403,
                    detail="Услуга не принадлежит указанной компании",
                )

        return context

    return Depends(dependency)


def with_permission_and_legal_entity_company_check(permission: str):
    async def dependency(
        relation_id: UUID = Path(..., description="ID связи компании и юрлица"),
        context: dict = Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context

        relation = await EntityCompanyRelation.get_or_none(
            entity_company_relation_id=relation_id
        ).prefetch_related("company")

        if not relation or str(relation.company_id) != str(context["company_id"]):
            raise HTTPException(
                status_code=403,
                detail="Связь не принадлежит компании пользователя или не найдена",
            )

        return context

    return Depends(dependency)


def with_permission_and_entity_company_check(permission: str):
    async def dependency(
        legal_entity_id: UUID = Path(..., description="ID юридического лица"),
        context: dict = Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context

        # Проверка, связано ли это юр. лицо с компанией пользователя
        is_related = await EntityCompanyRelation.exists(
            legal_entity_id=legal_entity_id, company_id=context["company"]
        )

        if not is_related:
            raise HTTPException(
                status_code=403,
                detail="Вы не можете изменять юридические лица другой компании",
            )

        return context

    return Depends(dependency)
