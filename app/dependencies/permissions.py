from typing import Dict, List, Type
from uuid import UUID
from tortoise.models import Model
from loguru import logger
from fastapi import HTTPException, Depends, Path
from app.handlers.depends import require_permission_in_context
from app.handlers.auth import get_current_user
from app.database.models import User, UserCompanyRelation, Permissions, EntityCompanyRelation, ActDetails, BillDetails


async def get_company_permissions_for_user(user: User) -> Dict[str, List[str]]:
    logger.debug(
        f"🧩 user: {user} | type: {type(user)} | has is_superadmin: {hasattr(user, 'is_superadmin')}")

    is_superadmin = getattr(user, "is_superadmin", False)
    if is_superadmin:
        logger.debug(
            "👑 Пользователь супер админ — возвращаем универсальные права")
        return {"*": ["*"]}

    logger.debug("🔒 Пользователь не суперадмин — ищем права по компаниям")

    relations = await UserCompanyRelation.filter(user_id=user.user_id).select_related("company", "role")

    company_permissions = {}

    for rel in relations:
        perms = await Permissions.filter(
            role_permission_relations__role=rel.role
        ).values_list("permission_id", flat=True)

        company_permissions[str(rel.company.company_id)] = list(perms)

    return company_permissions


def with_permission_and_company_check(permission: str):
    async def dependency(
        user_id: UUID = Path(..., description="ID пользователя"),
        context: dict = Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context

        related_user_ids = await UserCompanyRelation.filter(
            company=context["company"]
        ).values_list("user_id", flat=True)

        if user_id not in related_user_ids:
            raise HTTPException(
                status_code=403,
                detail="Вы не можете выполнять это действие над пользователями других компаний"
            )

        return context

    return Depends(dependency)


def with_exact_company_permission(permission: str):
    async def dependency(
        company_id: UUID = Path(..., description="ID компании"),
        user_data: dict = Depends(get_current_user),
    ):
        if user_data.get("is_superadmin"):
            return user_data

        if permission not in user_data.get("permissions", []):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        username = user_data["username"]

        relation_exists = await UserCompanyRelation.filter(
            user__username=username,
            company__company_id=company_id
        ).exists()

        if not relation_exists:
            raise HTTPException(
                status_code=403, detail="Нет доступа к компании")

        return user_data

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
            legal_entity_id=legal_entity_id,
            company_id=context["company"]
        )

        if not is_related:
            raise HTTPException(
                status_code=403,
                detail="Вы не можете изменять юридические лица другой компании"
            )

        return context

    return Depends(dependency)


def with_permission_and_seller_company_check(
    permission: str,
    model: Type[Model],
    model_name: str,
):

    def factory():
        return Path(..., description=f"ID {model_name}")

    async def dependency(
        context: dict = Depends(require_permission_in_context(permission)),
        model_id: UUID = Depends(factory)  # 👈 FastAPI сам свяжет с path
    ):
        if context.get("is_superadmin"):
            return context

        instance = await model.get_or_none(**{f"{model_name}_id": model_id}).prefetch_related("seller")
        if not instance:
            raise HTTPException(
                status_code=404, detail=f"{model_name.capitalize()} не найден")

        is_seller = await EntityCompanyRelation.exists(
            company_id=context["company"],
            legal_entity=instance.seller,
            relation_type="seller"
        )

        if not is_seller:
            raise HTTPException(
                status_code=403,
                detail=f"Вы не можете управлять {model_name} с чужим продавцом"
            )

        return context

    return Depends(dependency)


def with_permission_through_act(permission: str):
    async def dependency(
        act_detail_id: UUID = Path(...),
        context=Depends(require_permission_in_context(permission))
    ):
        if context.get("is_superadmin"):
            return context

        detail = await ActDetails.get_or_none(act_detail_id=act_detail_id).prefetch_related("act__seller")
        if not detail:
            raise HTTPException(
                status_code=404, detail="Деталь акта не найдена")

        is_seller = await EntityCompanyRelation.exists(
            company_id=context["company"],
            legal_entity=detail.act.seller,
            relation_type="seller"
        )

        if not is_seller:
            raise HTTPException(
                status_code=403,
                detail="Вы не можете работать с деталями акта чужой компании"
            )

        return context

    return Depends(dependency)


def with_permission_through_bill(permission: str):
    async def dependency(
        bill_detail_id: UUID = Path(...),
        context=Depends(require_permission_in_context(permission))
    ):
        if context.get("is_superadmin"):
            return context

        detail = await BillDetails.get_or_none(bill_detail_id=bill_detail_id).prefetch_related("bill__seller")
        if not detail:
            raise HTTPException(
                status_code=404, detail="Деталь акта не найдена")

        is_seller = await EntityCompanyRelation.exists(
            company_id=context["company"],
            legal_entity=detail.bill.seller,
            relation_type="seller"
        )

        if not is_seller:
            raise HTTPException(
                status_code=403,
                detail="Вы не можете работать с деталями акта чужой компании"
            )

        return context

    return Depends(dependency)
