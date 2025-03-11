import pytest
from app.database.models import BankAccount, LegalEntity


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_bank_account(seed_legal_entity):
    """Создает тестовое юридическое лицо, передавая объекты вместо ID."""

    # Получаем объекты из базы
    entity = await LegalEntity.get_or_none(legal_entity_id=seed_legal_entity["legal_entity_id"])

    if not entity:
        raise ValueError(
            "Ошибка: Не удалось получить объекты Company или LegalEntityType")

    # Создаем юридическое лицо, передавая объекты
    bank_account = await BankAccount.create(
        account_number="12345678901234567890",
        bank_name="Test Bank",
        bank_bic="123456789",
        bank_corr_account="98765432109876543210",
        legal_entity=entity
    )

    return {
        "bank_account_id": str(bank_account.bank_account_id),
        "account_number": bank_account.account_number,
        "bank_name": bank_account.bank_name,
        "bank_bic": bank_account.bank_bic,
        "bank_corr_account": bank_account.bank_corr_account,
        "legal_entity": bank_account.legal_entity
    }
