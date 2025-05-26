from decimal import Decimal

import pytest

from app.database.models import ActDetails, Acts, Contract, LegalEntity, Service


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_act(
    seed_legal_entity, seed_legal_entity_buyer, seed_contract, seed_company
):
    """Создает тестовое юридическое лицо, передавая объекты вместо ID."""

    # Получаем объекты из базы
    contract = await Contract.get_or_none(contract_id=seed_contract["contract_id"])

    if not contract:
        raise ValueError("Ошибка: Не удалось получить объект Contract")

    buyer = await LegalEntity.get_or_none(
        legal_entity_id=seed_legal_entity_buyer["legal_entity_id"]
    )

    seller = await LegalEntity.get_or_none(
        legal_entity_id=seed_legal_entity["legal_entity_id"]
    )
    if not buyer and seller:
        raise ValueError("Ошибка: Не удалось получить объект Contract")
    # Создаем юридическое лицо, передавая объекты
    act = await Acts.create(
        act_number="ACT-001",
        act_date=1700000000,
        contract=contract,
        buyer=buyer,
        seller=seller,
        company_id=seed_company["company_id"],
    )

    return {
        "act_id": str(act.act_id),
        "act_number": act.act_number,
        "act_date": act.act_date,
        "contract": str(act.contract.contract_id) if act.contract else None,
        "buyer": str(act.buyer.legal_entity_id),
        "seller": str(act.seller.legal_entity_id),
        "company": act.company,
    }


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_act_detail(seed_act, seed_service):
    """Создает тестовое юридическое лицо, передавая объекты вместо ID."""

    # Получаем объекты из базы
    act = await Acts.get_or_none(act_id=seed_act["act_id"])
    service = await Service.get_or_none(service_id=seed_service["service_id"])

    if not act or not service:
        raise ValueError("Ошибка: Не удалось получить объект Acts Services")

    # Создаем юридическое лицо, передавая объекты
    act_detail = await ActDetails.create(
        act=act, service=service, quantity=2, summ=Decimal(2 * 20), price=20
    )

    return {
        "act_detail_id": str(act_detail.act_detail_id),
        "act": act_detail.act,
        "service": act_detail.service,
        "quantity": act_detail.quantity,
        "summ": act_detail.summ,
        "price": act_detail.price,
    }
