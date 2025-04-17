from typing import Dict, List
from uuid import UUID
from loguru import logger
from fastapi import HTTPException, Depends, Path
from app.handlers.depends import require_permission_in_context
from app.database.models import User, UserCompanyRelation, Permissions, LegalEntity


async def get_company_permissions_for_user(user: User) -> Dict[str, List[str]]:
    if user.is_superadmin:
        logger.debug("Пользователь супер админ")
        return {"*": ["*"]}  # 💥 вот так правильно
    logger.debug("Пользователь не суперадмин")
    relations = await UserCompanyRelation.filter(user=user).select_related("company", "role")
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


def with_permission_and_exact_company(permission: str):
    async def dependency(
        company_id: UUID = Path(..., description="ID компании"),
        context: dict = Depends(require_permission_in_context(permission)),
    ):
        if context.get("is_superadmin"):
            return context

        if str(context["company"]) != str(company_id):
            raise HTTPException(
                status_code=403,
                detail="Вы не можете редактировать или удалять другие компании"
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

        entity = await LegalEntity.get_or_none(legal_entity_id=legal_entity_id).prefetch_related("company")
        if not entity:
            raise HTTPException(
                status_code=404, detail="Юридическое лицо не найдено")

        if str(entity.company.company_id) != str(context["company"]):
            raise HTTPException(
                status_code=403,
                detail="Вы не можете изменять юридические лица другой компании"
            )

        return context

    return Depends(dependency)
