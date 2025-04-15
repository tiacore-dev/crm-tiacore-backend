import pytest
from app.database.models import UserRole, LegalEntityType, ContractStatus, Permissions, RolePermissionRelation


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_role():
    role = await UserRole.create(
        role_name="Администратор"
    )
    return {
        "role_id": str(role.role_id),
        "role_name": role.role_name
    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_permission():
    permission = await Permissions.create(
        permission_id='test_permission',
        permission_name='Тестовое разрешение'
    )
    return {
        "permission_id": str(permission.permission_id),
        "role": permission.permission_name
    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_role_permission_relation(seed_role, seed_permission):
    role = await UserRole.get_or_none(role_id=seed_role['role_id'])
    permission = await Permissions.get_or_none(permission_id=seed_permission['permission_id'])
    relation = await RolePermissionRelation.create(
        role=role,
        permission=permission
    )
    return {
        "role_permission_id": str(relation.role_permission_id),
        "role": relation.role,
        "permission": relation.permission
    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
async def seed_role_manager():
    role = await UserRole.create(
        role_name="Менеджер"
    )
    return {
        "role_id": str(role.role_id),
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
    """Создает тестовый статус контракта."""
    contract_status = await ContractStatus.create(
        contract_status_id="active",
        status_name="Active"
    )
    return {
        "contract_status_id": str(contract_status.contract_status_id),
        "status_name": contract_status.status_name
    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_contract_status_updated():
    """Создает тестовый статус контракта."""
    contract_status = await ContractStatus.create(
        contract_status_id="waiting",
        status_name="Waiting"
    )
    return {
        "contract_status_id": str(contract_status.contract_status_id),
        "status_name": contract_status.status_name
    }
