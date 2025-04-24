from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from loguru import logger
from app.config import Settings
from app.utils.permissions_get import get_company_permissions_for_user
from app.database.models import User
from app.auth_schemas import bearer_scheme

# Конфигурация JWT
settings = Settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE_DAYS = int(settings.REFRESH_TOKEN_EXPIRE_DAYS)


# Создание токена


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Проверка токена


def create_refresh_token(data: dict):
    return create_access_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> dict:
    if not credentials or not credentials.credentials or credentials.credentials.strip() == "":
        logger.warning("❌ Отсутствует или пустой токен Authorization")
        raise HTTPException(status_code=401, detail="Missing or empty token")

    token = credentials.credentials.strip()

    return verify_token(token)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        permissions: list = payload.get("permissions", [])
        if username is None:
            logger.warning("❌ Токен не содержит 'sub'. Отказ в доступе.")
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "permissions": permissions}
    except JWTError as e:
        logger.warning(f"❌ Ошибка при декодировании токена: {str(e)}")
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        ) from e


async def login_handler(username: str, password: str):
    user = await User.get_or_none(username=username)

    if not user:
        logger.warning(f"🔐 Пользователь '{username}' не найден")
        return None

    if not user.check_password(password):
        logger.warning(f"🔐 Неверный пароль для пользователя '{username}'")
        return None

    company_permissions = await get_company_permissions_for_user(user)

    return user, company_permissions


async def require_superadmin(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> dict:
    if not credentials or not credentials.credentials.strip():
        logger.warning("❌ Отсутствует или пустой токен Authorization")
        raise HTTPException(status_code=401, detail="Missing or empty token")

    token = credentials.credentials.strip()
    user_data = verify_token(token)

    username = user_data.get("username")
    if not username:
        logger.warning("❌ Токен не содержит имя пользователя")
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await User.get_or_none(username=username)
    if not user:
        logger.warning(f"❌ Пользователь {username} не найден в базе")
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_superadmin:
        logger.warning(f"🚫 Пользователь {username} не является суперадмином")
        raise HTTPException(status_code=403, detail="Только для суперадминов")

    logger.info(f"✅ Суперадмин авторизован: {username}")
    return {
        "user": user.id,  # или user.username, что тебе удобно
        "username": username,
        "is_superadmin": True,
    }
