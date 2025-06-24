from uuid import uuid4

import pytest

from app.database.models import ContractStatus, Service


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_contract_status():
    """Создает тестовый статус контракта."""
    contract_status = await ContractStatus.create(id="active", name="Active")
    return contract_status


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_contract_status_updated():
    """Создает тестовый статус контракта."""
    contract_status = await ContractStatus.create(id="waiting", name="Waiting")
    return contract_status


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_service():
    """Добавляет тестового пользователя в базу перед тестом."""
    service = await Service.create(name="Test Service", company_id=uuid4())
    return service
