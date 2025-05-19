import json
from typing import Optional
from hashlib import sha256
from fastapi_cache import FastAPICache
from loguru import logger
from fastapi import HTTPException
from app.database.models import User
from app.utils.permissions_get import get_company_permissions_for_user


def custom_key_builder(
    func,
    namespace: str,
    request=None,
    response=None,
    args: Optional[list] = None,
    kwargs: Optional[dict] = None,
) -> str:
    args = args or []
    kwargs = kwargs or {}

    raw_key = f"{func.__module__}:{func.__name__}:{args}:{kwargs}"
    hashed = sha256(raw_key.encode()).hexdigest()
    return f"{namespace}:{hashed}" if namespace else hashed


def get_user_cache_key(email: str) -> str:
    hashed = sha256(email.encode()).hexdigest()
    return f"fastapi-cache:{hashed}"


async def save_user_to_cache(user, permissions: dict):
    key = get_user_cache_key(user.email)
    data = {
        "email": user.email,
        "user_id": str(user.user_id),
        "is_superadmin": user.is_superadmin,
        "permissions": permissions,
    }
    serialized = json.dumps(data)
    await FastAPICache.get_backend().set(key, serialized)
    logger.debug(
        f"[save_user_to_cache] Сохранили данные в кэш: key={key}, data={serialized}")
    return data


async def debug_cached_user_data(email: str):
    backend = FastAPICache.get_backend()
    key = get_user_cache_key(email)
    value = await backend.get(key)
    logger.debug(f"[debug_cached_user_data] Ключ: {key}")
    logger.debug(f"[debug_cached_user_data] Значение в кэше: {value}")


async def invalidate_user_cache(email: str):
    key = get_user_cache_key(email)
    logger.debug(f"[invalidate_user_cache] Удаляем ключ из кэша: {key}")
    await FastAPICache.clear(key)
    await debug_cached_user_data(email)


async def get_cached_user_data(email: str) -> dict:
    backend = FastAPICache.get_backend()
    key = get_user_cache_key(email)
    cached = await backend.get(key)
    if cached:
        logger.debug(f"[get_cached_user_data] HIT key={key}, value={cached}")
        return json.loads(cached)

    logger.debug(f"[get_cached_user_data] MISS key={key}. Берем из базы.")
    user = await User.get_or_none(email=email)
    if not user:
        logger.warning(
            f"[get_cached_user_data] Пользователь {email} не найден в базе.")
        raise HTTPException(
            status_code=500, detail="Пользователь не найден в базе")

    permissions = await get_company_permissions_for_user(user)

    data = {
        "email": email,
        "permissions": permissions,
        "is_superadmin": user.is_superadmin,
        "user_id": str(user.user_id),
    }

    serialized = json.dumps(data)
    await backend.set(key, serialized)
    logger.debug(
        f"[get_cached_user_data] Кэшируем key={key}, value={serialized}")
    return data
