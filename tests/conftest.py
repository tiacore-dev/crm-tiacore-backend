from uuid import uuid4

import pytest
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import AsyncClient
from tiacore_lib.handlers.auth_handler import create_access_token, create_refresh_token
from tiacore_lib.handlers.cache_handler import save_user_to_cache
from tortoise import Tortoise

from app import create_app
from app.config import ConfigName, _load_settings
from app.utils.db_helpers import drop_all_tables


@pytest.fixture(scope="session")
def test_settings():
    return _load_settings(ConfigName.TEST)


@pytest.fixture(scope="function")
async def test_app():
    app = create_app(config_name=ConfigName.TEST)
    FastAPICache.init(InMemoryBackend())
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    await Tortoise.close_connections()


@pytest.fixture(scope="function", autouse=True)
@pytest.mark.asyncio
async def setup_and_clean_db(test_settings):
    await Tortoise.init(
        config={
            "connections": {"default": test_settings.db_url},
            "apps": {
                "models": {
                    "models": ["app.database.models"],
                    "default_connection": "default",
                },
            },
        }
    )

    await Tortoise.generate_schemas()

    yield
    await drop_all_tables()  # 💥 удаляем все таблицы
    await Tortoise.close_connections()


pytest_plugins = [
    "tests.fixtures.acts",
    "tests.fixtures.bills",
    "tests.fixtures.contract",
    "tests.fixtures.bank_account",
    "tests.fixtures.company_relations",
    "tests.fixtures.names",
]


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def jwt_token_admin(test_settings):
    """Генерирует JWT токен для администратора."""
    token_data = {"sub": "admin"}
    await save_user_to_cache("admin", uuid4(), True, None, None, None)
    return {
        "access_token": create_access_token(token_data, test_settings),
        "refresh_token": create_refresh_token(token_data, test_settings),
    }
