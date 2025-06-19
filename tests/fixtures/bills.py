from uuid import uuid4

import pytest

from app.database.models import (
    BankAccount,
    BillDetails,
    Bills,
    Contract,
    Service,
)


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_bill(
    seed_contract: Contract,
    seed_bank_account: BankAccount,
):
    bill = await Bills.create(
        number="bill-001",
        date=1700000000,
        contract=seed_contract,
        bank_account=seed_bank_account,
        buyer_id=uuid4(),
        seller_id=uuid4(),
        company_id=uuid4(),
    )

    return bill


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_bill_detail(seed_bill: Bills, seed_service: Service):
    bill_detail = await BillDetails.create(
        bill=seed_bill, service=seed_service, quantity=2, summ=2000, price=20
    )

    return bill_detail
