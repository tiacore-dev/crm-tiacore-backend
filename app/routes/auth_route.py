from fastapi import APIRouter, Body, HTTPException
from jose import JWTError
from loguru import logger

from app.database.models import User
from app.handlers.auth import (
    create_access_token,
    create_refresh_token,
    login_handler,
    verify_token,
)
from app.pydantic_models.auth_models import (
    LoginRequest,
    TokenResponse,
)
from app.utils.permissions_get import get_company_permissions_for_user

auth_router = APIRouter()


@auth_router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    result = await login_handler(data.email, data.password)
    if not result:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    user, company_permissions = result
    logger.debug(f"Полученные разрешения: {company_permissions}")
    return TokenResponse(
        access_token=create_access_token({"sub": user.email}),
        refresh_token=create_refresh_token({"sub": user.email}),
        permissions=None if user.is_superadmin else company_permissions,
        is_superadmin=user.is_superadmin,
        user_id=user.user_id,
    )


@auth_router.post(
    "/refresh", response_model=TokenResponse, summary="Обновление Access Token"
)
async def refresh_access_token(data: dict = Body(...)):
    try:
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is required")

        payload = await verify_token(refresh_token)
        email = payload["email"]

        user = await User.get_or_none(email=email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        company_permissions = await get_company_permissions_for_user(user)

        return TokenResponse(
            access_token=create_access_token(
                {
                    "sub": email,
                }
            ),
            refresh_token=create_refresh_token({"sub": email}),
            permissions=None if user.is_superadmin else company_permissions,
            is_superadmin=user.is_superadmin,
            user_id=user.user_id,
        )

    except JWTError as exc:
        raise HTTPException(
            status_code=401, detail="Неверный или просроченный токен"
        ) from exc
