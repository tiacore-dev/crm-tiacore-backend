import pytest
from app.database.models import Contract, ContractStatus, LegalEntity


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_contract(seed_legal_entity, seed_legal_entity_buyer, seed_contract_status, seed_company):
    """Создает тестовое юридическое лицо, передавая объекты вместо ID."""

    # Получаем объекты из базы
    seller = await LegalEntity.get_or_none(legal_entity_id=seed_legal_entity["legal_entity_id"])
    buyer = await LegalEntity.get_or_none(legal_entity_id=seed_legal_entity_buyer["legal_entity_id"])
    status = await ContractStatus.get_or_none(contract_status_id=seed_contract_status['contract_status_id'])

    if not seller or not buyer or not status:
        raise ValueError(
            "Ошибка: Не удалось получить объекты Company или LegalEntityType")

    # Создаем юридическое лицо, передавая объекты
    contract = await Contract.create(
        contract_name="Test Contract",
        contract_date="123456789012",
        buyer=buyer,
        seller=seller,
        status=status,
        company_id=seed_company['company_id']
    )

    return {
        "contract_id": str(contract.contract_id),
        "contract_name": contract.contract_name,
        "contract_date": contract.contract_date,
        "buyer": contract.buyer,
        "seller": contract.seller,
        "status": contract.status,
        "company": contract.company
    }
