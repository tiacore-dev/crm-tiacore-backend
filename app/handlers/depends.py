from uuid import UUID
from typing import Optional
from loguru import logger
from fastapi import Depends, Query, HTTPException
from app.database.models import User
from app.handlers.auth import get_current_user


async def get_current_context(
    token_data: dict = Depends(get_current_user),
    company: Optional[UUID] = Query(None, description="ID компании")
):
    username = token_data["username"]
    permissions_map = token_data.get("permissions", {})

    is_token_superadmin = permissions_map.get("*") == ["*"]

    user = await User.get_or_none(username=username)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    # 👑 Суперадмин — ему всё можно
    if is_token_superadmin:
        if not user.is_superadmin:
            raise HTTPException(
                status_code=403, detail="Пользователь не является суперадмином")

        return {
            "user": user.user_id,
            "company": company,  # может быть None — это ок
            "role": "superadmin",
            "permissions": ["*"],
            "is_superadmin": True
        }

    # 🔐 Не суперадмин — без company не пущу
    if not company:
        logger.warning(
            f"Отказ в доступе: не указана компания для пользователя {username}")
        raise HTTPException(status_code=400, detail="Не указана компания")

    raw_permissions = permissions_map.get(str(company), [])
    return {
        "user": user.user_id,
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
