import os

import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app import create_app
from app.database.add_permissions import add_initial_permissions

load_dotenv()

# Порт и биндинг
PORT = 8000
PASSWORD = os.getenv("PASSWORD", " ")
CONFIG_NAME = os.getenv("CONFIG_NAME")


async def create_admin_user():
    from app.database.models import User, create_user

    # Проверяем, существует ли пользователь "admin"
    admin = await User.filter(email="admin").first()
    if not admin:
        await create_user(
            email="admin",
            password=PASSWORD,
            position="admin",
            full_name="Поликанова Виктория Сергеевна",
        )


async def create_test_data():
    from app.database.models import ContractStatus, LegalEntityType, UserRole

    try:
        await UserRole.get_or_create(
            role_name="Администратор", role_system_name="admin"
        )
        await UserRole.get_or_create(role_name="Пользователь", role_system_name="user")
        await LegalEntityType.get_or_create(
            legal_entity_type_id="ip", entity_name="Индивидуальный предприниматель"
        )
        await LegalEntityType.get_or_create(
            legal_entity_type_id="organization", entity_name="Организация"
        )
        await ContractStatus.get_or_create(
            contract_status_id="active", status_name="Активен"
        )
        await ContractStatus.get_or_create(
            contract_status_id="waiting", status_name="Ожидание"
        )
        await ContractStatus.get_or_create(
            contract_status_id="completed", status_name="Завершен"
        )
    except Exception as e:
        print(f"Exception: {e}")


app = create_app(config_name=CONFIG_NAME)


@app.on_event("startup")
async def startup_event():
    # Создаем администратора при запуске
    await add_initial_permissions()
    await create_admin_user()
    await create_test_data()
    # Используем имя докер контейнера
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    redis_client = redis.from_url(redis_url)
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(PORT), reload=True)
