from decimal import Decimal
from uuid import uuid4

import pytest

from app.database.models import ActDetails, Acts, Contract, Service


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_act(seed_contract: Contract):
    act = await Acts.create(
        number="ACT-001",
        date=1700000000,
        contract=seed_contract,
        buyer_id=uuid4(),
        seller_id=uuid4(),
        company_id=uuid4(),
    )

    return act


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_act_detail(seed_act: Acts, seed_service: Service):
    """Создает тестовое юридическое лицо, передавая объекты вместо ID."""

    # Создаем юридическое лицо, передавая объекты
    act_detail = await ActDetails.create(
        act=seed_act, service=seed_service, quantity=2, summ=Decimal(2 * 20), price=20
    )

    return act_detail
