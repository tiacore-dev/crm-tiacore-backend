from uuid import UUID
from typing import Optional
from loguru import logger
from fastapi import Depends, Query, HTTPException
from app.handlers.auth import get_current_user


async def get_current_context(
    token_data: dict = Depends(get_current_user),
    company: Optional[UUID] = Query(None, description="ID компании")
):
    email = token_data["email"]
    permissions_map = token_data.get("permissions", {})

    is_token_superadmin = token_data.get("is_superadmin")
    user_id = token_data["user_id"]

    # 👑 Суперадмин — ему всё можно
    if is_token_superadmin:

        return {
            "user": user_id,
            "company": company,  # может быть None — это ок
            "role": "superadmin",
            "permissions": ["*"],
            "is_superadmin": True
        }

    # 🔐 Не суперадмин — без company не пущу
    if not company:
        logger.warning(
            f"Отказ в доступе: не указана компания для пользователя {email}")
        raise HTTPException(status_code=400, detail="Не указана компания")

    raw_permissions = permissions_map.get(str(company), [])
    return {
        "user": user_id,
        "company": company,
        "role": None,
        "permissions": raw_permissions,
        "is_superadmin": False
    }


def require_permission_in_context(permission: str):
    async def dependency(ctx=Depends(get_current_context)):
        if ctx["is_superadmin"] or permission in ctx["permissions"]:
            return ctx
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return dependency
