import pytest
from app.database.models import Bills, BillDetails, Contract,  Service, BankAccount


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_bill(seed_contract, seed_bank_account):
    """Создает тестовый счет, передавая объекты вместо ID."""

    # Получаем объекты из базы
    contract = await Contract.get(contract_id=seed_contract["contract_id"])
    bank_account = await BankAccount.get(bank_account_id=seed_bank_account["bank_account_id"])

    # Создаем счет, передавая объекты
    bill = await Bills.create(
        bill_number="bill-001",
        bill_date=1700000000,
        contract=contract,  # 👈 Передаем объект, а не ID
        bank_account=bank_account  # 👈 Передаем объект, а не ID
    )

    return {
        "bill_id": str(bill.bill_id),
        "bill_number": bill.bill_number,
        "bill_date": bill.bill_date,
        # 👈 Теперь это UUID, а не объект
        "contract": str(bill.contract.contract_id),
        # 👈 Теперь это UUID, а не объект
        "bank_account": str(bill.bank_account.bank_account_id)
    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_bill_detail(seed_bill, seed_service):
    """Создает тестовую деталь счета, передавая объекты вместо ID."""

    # Получаем объекты из базы
    bill = await Bills.get_or_none(bill_id=seed_bill["bill_id"])
    service = await Service.get_or_none(service_id=seed_service['service_id'])

    if not bill or not service:
        raise ValueError(
            "Ошибка: Не удалось получить объект Bills или Services")

    # Создаем деталь счета, передавая объекты
    bill_detail = await BillDetails.create(
        bill=bill,
        service=service,
        quantity=2,
        summ=2000
    )

    return {
        "bill_detail_id": str(bill_detail.bill_detail_id),
        "bill": str(bill.bill_id),  # ✅ Теперь передаем строковый UUID
        "service": str(service.service_id),  # ✅ Теперь передаем строковый UUID
        "quantity": bill_detail.quantity,
        "summ": bill_detail.summ
    }
