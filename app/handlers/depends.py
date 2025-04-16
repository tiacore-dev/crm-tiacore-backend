from uuid import UUID
from fastapi import Depends, Query, HTTPException
from app.database.models import User
from app.handlers.auth import get_current_user


async def get_current_context(
    token_data: dict = Depends(get_current_user),
    company: UUID = Query(..., description="ID компании")
):
    username = token_data["username"]
    permissions_map = token_data.get("permissions", {})

    raw_permissions = permissions_map.get(str(company), [])
    is_token_superadmin = permissions_map.get("*") == ["*"]

    user = await User.get_or_none(username=username)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    if is_token_superadmin:
        if not user.is_superadmin:
            raise HTTPException(
                status_code=403, detail="Пользователь не является суперадмином"
            )

        return {
            "user": user,
            "company": company,
            "role": "superadmin",

            "permissions": ["*"],
            "is_superadmin": True
        }

    return {
        "user": user,
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
