from datetime import timedelta
import pytest
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi.testclient import TestClient
from tortoise import Tortoise
from app import create_app
from app.database.models import create_user, Service
from app.handlers.auth import create_access_token, create_refresh_token, login_handler
from app.config import Settings

settings = Settings()


@pytest.fixture(scope="session")
def test_app():
    """Фикстура для тестового приложения."""
    app = create_app(config_name="Test")

    # ✨ ИНИЦИАЛИЗИРУЕМ КЭШ ЯВНО
    FastAPICache.init(InMemoryBackend())

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

pytest_plugins = [
    "tests.fixtures.names",  # Фикстуры, связанные с именами, статусами, ролями
    "tests.fixtures.company_relations",  # Фикстуры для компаний и связей
    "tests.fixtures.legal_entity",  # Фикстуры для юридических лиц
    "tests.fixtures.contract",
    "tests.fixtures.bank_account",
    "tests.fixtures.acts",
    "tests.fixtures.bills",
    "tests.fixtures.permissions"
]


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_user():
    """Добавляет тестового пользователя в базу перед тестом."""
    user = await create_user(
        email="test_user",
        password="qweasdzcx",
        position="user",
        full_name="Test User"
    )
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "position": user.position,
        "full_name": user.full_name
    }


@pytest.mark.usefixtures("test_app")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_admin():
    """Добавляет тестового администратора в базу перед тестом."""
    admin = await create_user(
        email="test_admin",
        password="adminpass",
        position="admin",
        full_name="Test Admin"
    )
    admin.is_superadmin = True
    await admin.save()
    return {
        "user_id": str(admin.user_id),
        "email": admin.email,
        "position": admin.position,
        "full_name": admin.full_name
    }


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def jwt_token_user(seed_user):
    """Генерирует JWT токен для обычного пользователя."""
    token_data = {
        "sub": seed_user["email"]
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
        "sub": seed_admin["email"]
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data)
    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_service(seed_company):
    """Добавляет тестового пользователя в базу перед тестом."""
    service = await Service.create(
        service_name="Test Service",
        company_id=seed_company['company_id']
    )
    return {
        "service_id": str(service.service_id),
        "service_name": service.service_name,
        "company": str(service.company)
    }


@pytest.fixture
def get_token_for_user():
    # по умолчанию пароль фиксированный
    async def _get_token(user, password="123"):
        auth_result = await login_handler(user.email, password)
        if not auth_result:
            raise Exception(
                f"Не удалось залогиниться для пользователя {user.email}")

        user_obj, company_permissions = auth_result

        token_data = {
            "sub": user_obj.email,
        }

        token = create_access_token(
            token_data, expires_delta=timedelta(minutes=30))
        return token
    return _get_token
