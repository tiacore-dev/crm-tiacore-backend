from fastapi import APIRouter, Body, HTTPException, Depends
from jose import JWTError
from app.handlers.auth import login_handler, create_refresh_token, create_access_token, verify_token
from app.utils.permissions_get import get_company_permissions_for_user
from app.handlers.depends import get_current_context
from app.database.models import User
from app.pydantic_models.auth_models import TokenResponse, LoginRequest


auth_router = APIRouter()


@auth_router.post("/token", response_model=TokenResponse)
async def login(data: LoginRequest):
    result = await login_handler(data.email, data.password)
    if not result:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    user, company_permissions = result
    return TokenResponse(
        access_token=create_access_token({
            "sub": user.email
        }),
        refresh_token=create_refresh_token({"sub": user.email}),
        permissions=None if user.is_superadmin else company_permissions,
        is_superadmin=user.is_superadmin,

    )


@auth_router.post("/refresh", response_model=TokenResponse, summary="Обновление Access Token")
async def refresh_access_token(data: dict = Body(...)):
    try:
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=400, detail="Refresh token is required")

        payload = await verify_token(refresh_token)
        email = payload["email"]

        user = await User.get_or_none(email=email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        company_permissions = await get_company_permissions_for_user(user)

        return TokenResponse(
            access_token=create_access_token({
                "sub": email,
            }),
            refresh_token=create_refresh_token({"sub": email}),
            permissions=None if user.is_superadmin else company_permissions,
            is_superadmin=user.is_superadmin,
            user_id=user.user_id
        )

    except JWTError as exc:
        raise HTTPException(
            status_code=401, detail="Неверный или просроченный токен"
        ) from exc


@auth_router.get("/superadmin", response_model=bool, summary="Проверка, является ли пользователь суперадмином")
async def is_superadmin(context=Depends(get_current_context)):
    return bool(context['is_superadmin'])
