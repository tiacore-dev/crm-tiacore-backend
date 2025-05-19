from datetime import datetime, timedelta
from hashlib import sha256
from jose import JWTError, jwt
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
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
JWT_EXPIRATION_HOURS = int(settings.JWT_EXPIRATION_HOURS)


def custom_key_builder(
    func,
    args: list,
    kwargs: dict,
    namespace: str = "",
) -> str:
    """
    Генерация ключа кэша, совместимая с fastapi-cache.
    """
    raw_key = f"{func.__module__}:{func.__name__}:{args}:{kwargs}"
    hashed = sha256(raw_key.encode()).hexdigest()
    return f"{namespace}:{hashed}" if namespace else hashed


def generate_token(payload: dict, expires_in_hours: int = JWT_EXPIRATION_HOURS) -> str:
    payload = {
        **payload,
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"❌ Ошибка при декодировании токена: {str(e)}")
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        ) from e


async def debug_cached_user_data(email: str):
    backend = FastAPICache.get_backend()
    key = custom_key_builder(get_cached_user_data, args=[
                             email], kwargs={}, namespace="fastapi-cache")
    value = await backend.get(key)
    logger.debug(f"[debug_cached_user_data] Ключ: {key}")
    logger.debug(f"[debug_cached_user_data] Значение в кэше: {value}")


async def invalidate_user_cache(email: str):
    key = custom_key_builder(get_cached_user_data, args=[email], kwargs={})
    logger.debug(f"[invalidate_user_cache] Invalidate cache for key: {key}")
    await FastAPICache.clear(key)

    await debug_cached_user_data(email)


@cache(expire=300, key_builder=custom_key_builder)  # кэш на 5 минут
async def get_cached_user_data(email: str) -> dict:
    user = await User.get_or_none(email=email)
    if not user:
        raise HTTPException(
            status_code=500, detail="Пользователь не найден в базе")

    permissions = await get_company_permissions_for_user(user)
    logger.debug(
        f"[get_cached_user_data] email={email}, permissions={permissions}")

    return {
        "email": email,
        "permissions": permissions,
        "is_superadmin": user.is_superadmin,
        "user_id": user.user_id
    }


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Проверка токена


def create_refresh_token(data: dict):
    return create_access_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> dict:
    if not credentials or not credentials.credentials or credentials.credentials.strip() == "":
        logger.warning("❌ Отсутствует или пустой токен Authorization")
        raise HTTPException(status_code=401, detail="Missing or empty token")

    token = credentials.credentials.strip()

    token_data = await verify_token(token)
    return token_data


async def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            logger.warning("❌ Токен не содержит 'sub'. Отказ в доступе.")
            raise HTTPException(status_code=401, detail="Invalid token")

        token_data = await get_cached_user_data(email)  # 💥 БЕРЕМ ИЗ КЭША

        return token_data

    except JWTError as e:
        logger.warning(f"❌ Ошибка при декодировании токена: {str(e)}")
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        ) from e


async def login_handler(email: str, password: str):
    user = await User.get_or_none(email=email)

    if not user:
        logger.warning(f"🔐 Пользователь '{email}' не найден")
        return None

    if not user.check_password(password):
        logger.warning(f"🔐 Неверный пароль для пользователя '{email}'")
        return None

    if not user.is_verified and not user.is_superadmin:
        raise HTTPException(
            status_code=403, detail="Необходимо верифицировать email")

    company_permissions = await get_company_permissions_for_user(user)

    return user, company_permissions


async def require_superadmin(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> dict:
    if not credentials or not credentials.credentials.strip():
        logger.warning("❌ Отсутствует или пустой токен Authorization")
        raise HTTPException(status_code=401, detail="Missing or empty token")

    token = credentials.credentials.strip()
    user_data = await verify_token(token)

    email = user_data.get("email")
    if not email:
        logger.warning("❌ Токен не содержит имя пользователя")
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_data['is_superadmin']:
        logger.warning(f"🚫 Пользователь {email} не является суперадмином")
        raise HTTPException(status_code=403, detail="Только для суперадминов")

    logger.info(f"✅ Суперадмин авторизован: {email}")
    return {
        "user": user_data['user_id'],
        "email": email,
        "is_superadmin": True,
    }
