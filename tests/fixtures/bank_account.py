from uuid import uuid4

import pytest

from app.database.models import BankAccount


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_bank_account():
    # Создаем юридическое лицо, передавая объекты
    bank_account = await BankAccount.create(
        number="12345678901234567890",
        bank_name="Test Bank",
        bank_bic="123456789",
        bank_corr_account="98765432109876543210",
        legal_entity_id=uuid4(),
    )

    return bank_account
