from fastapi import APIRouter, Body, HTTPException, Query, Depends
from jose import JWTError
from loguru import logger
from app.handlers.auth import (
    login_handler,
    create_refresh_token,
    create_access_token,
    verify_token,
    verify_jwt_token,
    generate_token,
    get_current_user
)
from app.utils.permissions_get import get_company_permissions_for_user
from app.utils.verification import send_email
from app.database.models import User, create_user, UserCompanyRelation
from app.pydantic_models.auth_models import (
    TokenResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    InviteRequest
)
from app.config import Settings

settings = Settings()


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


@auth_router.post("/register", response_model=RegisterResponse)
async def register(data: RegisterRequest):
    user = await create_user(email=data.email, password=data.password, full_name=data.full_name, position=data.position)
    token = generate_token({"user_id": str(user.user_id), "sub": data.email})
    logger.info(
        f"Пользователь зарегистрирован: {user.email}, user_id={user.user_id}")
    verification_link = f"{settings.BACK_ORIGIN}/api/auth/verify-email?token={token}"
    body = f"""
    Здравствуйте!

    Пожалуйста, подтвердите свою почту, перейдя по ссылке:
    {verification_link}

    Если это были не вы, проигнорируйте это письмо.
    """
    send_email(user.email,  body)
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
    payload = verify_jwt_token(token)
    user_id = payload.get("sub")
    if not user_id:
        logger.warning(f"Попытка верификации с некорректным токеном: {token}")
        raise HTTPException(status_code=400, detail="Проблема с токеном")

    user = await User.get_or_none(user_id=user_id)
    if not user:
        logger.warning(
            f"Пользователь не найден при верификации почты, user_id={user_id}")
        raise HTTPException(status_code=400, detail="Пользователь не найден")

    if user.is_verified:
        logger.info(f"Почта уже подтверждена ранее, user_id={user.user_id}")
        return {"message": "Почта уже подтверждена"}

    user.is_verified = True
    await user.save()

    logger.info(f"Почта успешно подтверждена, user_id={user.user_id}")
    return {"message": "Почта успешно подтверждена!"}


@auth_router.post("/invite", status_code=201)
async def invite_user(data: InviteRequest, _=Depends(get_current_user)):
    payload = {
        "sub": data.email,
        "company_id": str(data.company_id), "role_id": str(data.role_id)}
    token = generate_token(payload)
    verification_link = f"{settings.FRONT_ORIGIN}/invite?token={token}&email={data.email}"
    body = f"""
    Здравствуйте!

    Вас пригласили в Tiacore CRM. Для регистрации перейдите по ссылке:

    {verification_link}

    """
    send_email(data.email,  body)
    return {"invite_link": verification_link}


@auth_router.post("/register-with-token", response_model=TokenResponse, status_code=201)
async def register_with_token(data: RegisterRequest, token: str = Query(...)):

    user = await create_user(email=data.email, password=data.password, full_name=data.full_name, position=data.position)
    user.is_verified = True
    await user.save()

    token_data = verify_jwt_token(token)
    company_id = token_data.get('company_id')
    role_id = token_data.get('role_id')
    if not company_id or not role_id:
        raise HTTPException(status_code=400, detail="Invalid invitation token")

    await UserCompanyRelation.create(user=user, company_id=company_id, role_id=role_id)
    return TokenResponse(
        access_token=create_access_token({
            "sub": user.email
        }),
        refresh_token=create_refresh_token({"sub": user.email}),
        permissions=None if user.is_superadmin else await get_company_permissions_for_user(user),
        is_superadmin=user.is_superadmin,
        user_id=user.user_id
    )
