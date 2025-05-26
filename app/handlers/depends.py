from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Query
from loguru import logger

from app.database.models import UserCompanyRelation
from app.handlers.auth import get_current_user


async def get_current_context(
    token_data: dict = Depends(get_current_user),
    company: Optional[UUID] = Query(None, description="ID компании"),
):
    permissions_map = token_data.get("permissions", {})
    is_token_superadmin = token_data.get("is_superadmin")
    user_id = token_data["user_id"]

    if is_token_superadmin:
        return {
            "user": user_id,
            "company": company,
            "role": "superadmin",
            "permissions": ["*"],
            "is_superadmin": True,
            "has_relations": True,
        }

    relations = await UserCompanyRelation.filter(user_id=user_id).all()
    has_relations = bool(relations)

    permissions = []
    if company:
        permissions = permissions_map.get(str(company), [])

    return {
        "user": user_id,
        "company": company,
        "role": None,
        "permissions": permissions,
        "is_superadmin": False,
        "has_relations": has_relations,
    }


def require_permission_in_context(permission: str):
    async def dependency(ctx=Depends(get_current_context)):
        if ctx["is_superadmin"]:
            return ctx
        if not ctx["has_relations"]:
            # Если у пользователя нет вообще связей с компаниями — разрешаем молча
            logger.info(
                f"""Пользователь {ctx["user"]} без связей — 
                доступ разрешён без проверки прав"""
            )
            return ctx
        if permission in ctx["permissions"]:
            return ctx
        logger.warning(
            f"Недостаточно прав для пользователя {ctx['user']}, требуется: {permission}"
        )
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    return dependency
