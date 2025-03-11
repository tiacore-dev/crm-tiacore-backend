import pytest
from app.database.models import Acts, ActDetails, Contract, Service


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_act(seed_contract):
    """Создает тестовое юридическое лицо, передавая объекты вместо ID."""

    # Получаем объекты из базы
    contract = await Contract.get_or_none(contract_id=seed_contract["contract_id"])

    if not contract:
        raise ValueError(
            "Ошибка: Не удалось получить объект Contract")

    # Создаем юридическое лицо, передавая объекты
    act = await Acts.create(
        act_number="ACT-001",
        act_date=1700000000,
        contract=contract
    )

    return {
        "act_id": str(act.act_id),
        "act_number": act.act_number,
        "act_date": act.act_date,
        "contract": act.contract
    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_act_detail(seed_act, seed_service):
    """Создает тестовое юридическое лицо, передавая объекты вместо ID."""

    # Получаем объекты из базы
    act = await Acts.get_or_none(act_id=seed_act["act_id"])
    service = await Service.get_or_none(service_id=seed_service['service_id'])

    if not act or not service:
        raise ValueError(
            "Ошибка: Не удалось получить объект Acts Services")

    # Создаем юридическое лицо, передавая объекты
    act_detail = await ActDetails.create(
        act=act,
        service=service,
        quantity=2,
        summ=2000
    )

    return {
        "act_detail_id": str(act_detail.act_detail_id),
        "act": act_detail.act,
        "service": act_detail.service,
        "quantity": act_detail.quantity,
        "summ": act_detail.summ
    }
