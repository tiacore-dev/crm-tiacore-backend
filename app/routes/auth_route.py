from fastapi import APIRouter, Body, HTTPException, Depends
from jose import JWTError, jwt
from loguru import logger
from app.handlers import login_handler, create_refresh_token, create_access_token
from app.handlers.auth import SECRET_KEY, ALGORITHM, get_current_user
from app.pydantic_models.auth_models import TokenResponse, LoginRequest

auth_router = APIRouter()


@auth_router.get("/protected", summary="Пример защищённого эндпоинта")
async def protected_route(username: str = Depends(get_current_user)):
    return {"message": "Доступ разрешён", "user": username}


@auth_router.post("/token", response_model=TokenResponse, summary="Авторизация пользователя")
async def login(data: LoginRequest):
    user = await login_handler(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    return TokenResponse(
        access_token=create_access_token({"sub": data.username}),
        refresh_token=create_refresh_token({"sub": data.username}),
        token_type="bearer"
    )


@auth_router.post("/refresh", response_model=TokenResponse, summary="Обновление Access Token")
async def refresh_access_token(data: dict = Body(...)):
    try:

        refresh_token = data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=400, detail="Refresh token is required")
        logger.info(f"Полученный токен: {refresh_token}")
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        logger.info(f"Полученный токен: {refresh_token}")
        if not username:
            raise HTTPException(status_code=401, detail="Неверный токен")

        new_access_token = create_access_token({"sub": username})
        new_refresh_token = create_refresh_token({"sub": username})

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    except JWTError as exc:
        raise HTTPException(
            status_code=401, detail="Неверный или просроченный токен") from exc
