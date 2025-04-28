from fastapi import APIRouter, Body, HTTPException, Query
from jose import JWTError
from loguru import logger
from app.handlers.auth import login_handler, create_refresh_token, create_access_token, verify_token, verify_email_token, generate_email_token
from app.utils.permissions_get import get_company_permissions_for_user
from app.utils.verification import send_verification_email
from app.database.models import User, create_user
from app.pydantic_models.auth_models import TokenResponse, LoginRequest, RegisterRequest, RegisterResponse


auth_router = APIRouter()


@auth_router.post("/token", response_model=TokenResponse)
async def login(data: LoginRequest):
    result = await login_handler(data.email, data.password)
    if not result:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    user, company_permissions = result
    logger.debug(f"Полученные разрешения: {company_permissions}")
    return TokenResponse(
        access_token=create_access_token({
            "sub": user.email
        }),
        refresh_token=create_refresh_token({"sub": user.email}),
        permissions=None if user.is_superadmin else company_permissions,
        is_superadmin=user.is_superadmin,
        user_id=user.user_id
    )


@auth_router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest):
    user = await create_user(email=data.email, password=data.password, full_name=data.full_name, position=data.position)
    token = generate_email_token(user.user_id)
    send_verification_email(user.email, token)
    return RegisterResponse(user_id=user.user_id)


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


@auth_router.get("/verify-email")
async def verify_email(token: str = Query(...)):
    payload = verify_email_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Проблема с токеном")

    user = await User.get_or_none(user_id=user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Пользователь не найден")

    if user.is_verified:
        return {"message": "Почта уже подтверждена"}

    user.is_verified = True
    await user.save()

    return {"message": "Почта успешно подтверждена!"}
