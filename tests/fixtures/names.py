import pytest
from app.database.models import UserRole, LegalEntityType, ContractStatus


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_role():
    role = await UserRole.create(
        role_id="admin",
        role_name="Администратор"
    )
    return {
        "role_id": role.role_id,
        "role_name": role.role_name
    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
async def seed_role_manager():
    role = await UserRole.create(
        role_id="manager",
        role_name="Менеджер"
    )
    return {
        "role_id": role.role_id,
        "role_name": role.role_name
    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_legal_entity_type():
    """Создает тестовый тип юридического лица."""
    entity_type = await LegalEntityType.create(
        legal_entity_type_id="ooo",
        entity_name="ООО"
    )
    return {
        "legal_entity_type_id": str(entity_type.legal_entity_type_id),
        "entity_name": entity_type.entity_name
    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_contract_status():
    """Создает тестовый тип юридического лица."""
    contract_status = await ContractStatus.create(
        status_name="ООО"
    )
    return {
        "contract_status_id": str(contract_status.contract_status_id),
        "status_name": contract_status.status_name
    }
