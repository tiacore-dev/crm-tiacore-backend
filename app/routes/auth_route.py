from fastapi import APIRouter, Form, HTTPException, Depends
from jose import JWTError, jwt
from app.handlers import login_handler, create_refresh_token, create_access_token
from app.handlers.auth import SECRET_KEY, ALGORITHM, get_current_user
from app.pydantic_models.auth_models import TokenResponse, LoginRequest

auth_router = APIRouter()


@auth_router.get("/protected", summary="Пример защищённого эндпоинта")
async def protected_route(token: str = Depends(get_current_user)):
    return {"message": "Доступ разрешён", "token": token}


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
async def refresh_token(token: str = Form(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

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
