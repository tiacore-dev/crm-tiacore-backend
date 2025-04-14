import pytest
from httpx import AsyncClient
from tortoise import Tortoise
from app import create_app
from app.database.models import create_user, Service
from app.handlers.auth import create_access_token, create_refresh_token
from app.config import Settings

settings = Settings()


@pytest.fixture
async def test_app():
    app = create_app(config_name="Test")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function", autouse=True)
@pytest.mark.asyncio
async def setup_and_clean_db():
    await Tortoise.init(config={
        "connections": {"default": settings.TEST_DATABASE_URL},
        "apps": {
            "models": {
                "models": ["app.database.models"],
                "default_connection": "default",
            },
        },
    })
    await Tortoise.generate_schemas()

    for model in reversed(list(Tortoise.apps.get("models", {}).values())):
        try:
            await model.all().delete()
        except Exception:
            pass

    yield
    await Tortoise.close_connections()

pytest_plugins = [
    "tests.fixtures.names",  # Фикстуры, связанные с именами, статусами, ролями
    "tests.fixtures.company_relations",  # Фикстуры для компаний и связей
    "tests.fixtures.legal_entity",  # Фикстуры для юридических лиц
    "tests.fixtures.contract",
    "tests.fixtures.bank_account",
    "tests.fixtures.acts",
    "tests.fixtures.bills"
]


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_user():
    """Добавляет тестового пользователя в базу перед тестом."""
    user = await create_user(
        username="test_user",
        password="qweasdzcx",
        position="user",
        full_name="Test User"
    )
    return {
        "user_id": str(user.user_id),
        "username": user.username,
        "position": user.position,
        "full_name": user.full_name
    }


@pytest.mark.usefixtures("test_app")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_admin():
    """Добавляет тестового администратора в базу перед тестом."""
    admin = await create_user(
        username="test_admin",
        password="adminpass",
        position="admin",
        full_name="Test Admin"
    )
    return {
        "user_id": str(admin.user_id),
        "username": admin.username,
        "position": admin.position,
        "full_name": admin.full_name
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


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_service():
    """Добавляет тестового пользователя в базу перед тестом."""
    service = await Service.create(
        service_name="Test Service"
    )
    return {
        "service_id": str(service.service_id),
        "service_name": service.service_name

    }
