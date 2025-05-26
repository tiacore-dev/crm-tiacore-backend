import pytest

from app.database.models import (
    BankAccount,
    BillDetails,
    Bills,
    Contract,
    LegalEntity,
    Service,
)


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_bill(
    seed_legal_entity,
    seed_legal_entity_buyer,
    seed_contract,
    seed_bank_account,
    seed_company,
):
    """Создает тестовый счет, передавая объекты вместо ID."""

    # Получаем объекты из базы
    contract = await Contract.get(contract_id=seed_contract["contract_id"])
    bank_account = await BankAccount.get(
        bank_account_id=seed_bank_account["bank_account_id"]
    )
    buyer = await LegalEntity.get_or_none(
        legal_entity_id=seed_legal_entity_buyer["legal_entity_id"]
    )
    seller = await LegalEntity.get_or_none(
        legal_entity_id=seed_legal_entity["legal_entity_id"]
    )
    if not buyer and seller:
        raise ValueError("Ошибка: Не удалось получить объект Contract")
    # Создаем счет, передавая объекты
    bill = await Bills.create(
        bill_number="bill-001",
        bill_date=1700000000,
        contract=contract,
        bank_account=bank_account,
        buyer=buyer,
        seller=seller,
        company_id=seed_company["company_id"],
    )

    return {
        "bill_id": str(bill.bill_id),
        "bill_number": bill.bill_number,
        "bill_date": bill.bill_date,
        "contract": str(bill.contract.contract_id) if bill.contract else None,
        "bank_account": str(bill.bank_account.bank_account_id),
        "buyer": str(bill.buyer.legal_entity_id),
        "seller": str(bill.seller.legal_entity_id),
        "company": bill.company,
    }


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_bill_detail(seed_bill, seed_service):
    """Создает тестовую деталь счета, передавая объекты вместо ID."""

    # Получаем объекты из базы
    bill = await Bills.get_or_none(bill_id=seed_bill["bill_id"])
    service = await Service.get_or_none(service_id=seed_service["service_id"])

    if not bill or not service:
        raise ValueError("Ошибка: Не удалось получить объект Bills или Services")

    # Создаем деталь счета, передавая объекты
    bill_detail = await BillDetails.create(
        bill=bill, service=service, quantity=2, summ=2000, price=20
    )

    return {
        "bill_detail_id": str(bill_detail.bill_detail_id),
        "bill": str(bill.bill_id),  # ✅ Теперь передаем строковый UUID
        "service": str(service.service_id),  # ✅ Теперь передаем строковый UUID
        "quantity": bill_detail.quantity,
        "summ": bill_detail.summ,
        "price": bill_detail.price,
    }
