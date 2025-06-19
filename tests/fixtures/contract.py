from uuid import uuid4

import pytest

from app.database.models import Contract, ContractStatus


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_contract(seed_contract_status: ContractStatus):
    # Создаем юридическое лицо, передавая объекты
    contract = await Contract.create(
        name="Test Contract",
        date="123456789012",
        buyer_id=uuid4(),
        seller_id=uuid4(),
        status=seed_contract_status,
        company_id=uuid4(),
    )

    return contract
