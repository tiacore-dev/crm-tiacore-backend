import pytest
from fastapi.testclient import TestClient
from tortoise import Tortoise
from app import create_app
from app.database.models import create_user
from app.handlers.auth import create_access_token, create_refresh_token
from app.config import Settings

settings = Settings()


@pytest.fixture(scope="session")
def test_app():
    """Фикстура для тестового приложения."""
    app = create_app(config_name="Test")
    client = TestClient(app)

    yield client  # Отдаём клиент тестам

    # Закрываем соединения после тестов
    import asyncio
    asyncio.run(Tortoise.close_connections())


@pytest.fixture(scope="function", autouse=True)
@pytest.mark.asyncio
async def setup_db():
    """Гарантируем, что Tortoise ORM инициализирован перед тестами."""
    await Tortoise.init(config={
        # Используем in-memory базу
        "connections": {"default": "sqlite://:memory:"},
        "apps": {
            "models": {
                "models": ["app.database.models"],
                "default_connection": "default",
            },
        },
    })
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_user():
    """Добавляет тестового пользователя в базу перед тестом."""
    user = await create_user(
        username="test_user",
        password="qweasdzcx",
        role="user",
        full_name="Test User"
    )
    return {
        "user_id": str(user.user_id),
        "username": user.username,
        "role": user.role
    }


@pytest.mark.usefixtures("test_app")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_admin():
    """Добавляет тестового администратора в базу перед тестом."""
    admin = await create_user(
        username="test_admin",
        password="adminpass",
        role="admin",
        full_name="Test Admin"
    )
    return {
        "user_id": str(admin.user_id),
        "username": admin.username,
        "role": admin.role
    }


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def jwt_token_user(seed_user):
    """Генерирует JWT токен для обычного пользователя."""
    token_data = {
        "sub": seed_user["username"]
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data)
    }


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def jwt_token_admin(seed_admin):
    """Генерирует JWT токен для администратора."""
    token_data = {
        "sub": seed_admin["username"]
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data)
    }
