from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.database.models import Contract, ContractStatus


@pytest.mark.asyncio
async def test_add_contract(
    test_app: AsyncClient,
    jwt_token_admin,
    seed_contract_status: ContractStatus,
):
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    form_data = {
        "contract_name": "Test Contract",
        "contract_date": "1710000000",
        "buyer": str(uuid4()),
        "seller": str(uuid4()),
        "comment": "Test contract comment",
        "status": str(seed_contract_status.id),
        "company": str(uuid4()),
    }

    response = await test_app.post(
        "/api/contracts/add",
        data=form_data,
        headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 201, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    data = response.json()
    contract = await Contract.filter(name="Test Contract").first()
    if contract:
        assert data["contract_id"] == str(contract.id)


@pytest.mark.asyncio
async def test_edit_contract(
    test_app: AsyncClient,
    jwt_token_admin,
    seed_contract: Contract,
    seed_contract_status_updated: ContractStatus,
):
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    form_data = {
        "contract_name": "Updated Contract Name",
        "comment": "Updated comment",
        "status": str(seed_contract_status_updated.id),
    }

    response = await test_app.patch(
        f"/api/contracts/{seed_contract.id}",
        data=form_data,
        headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    updated_contract = (
        await Contract.filter(id=seed_contract.id).first().prefetch_related("status")
    )
    if updated_contract:
        assert updated_contract.name == "Updated Contract Name"
        assert updated_contract.comment == "Updated comment"
        assert updated_contract.status.id == seed_contract_status_updated.id


@pytest.mark.asyncio
async def test_view_contract(
    test_app: AsyncClient, jwt_token_admin, seed_contract: Contract
):
    """Тест просмотра информации о контракте."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get(f"/api/contracts/{seed_contract.id}", headers=headers)

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    response_data = response.json()
    assert response_data["contract_id"] == str(seed_contract.id)
    assert response_data["contract_name"] == seed_contract.name


@pytest.mark.asyncio
async def test_delete_contract(
    test_app: AsyncClient, jwt_token_admin, seed_contract: Contract
):
    """Тест удаления контракта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.delete(
        f"/api/contracts/{seed_contract.id}", headers=headers
    )

    assert response.status_code == 204, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    # Проверяем, что контракт удалён
    deleted_contract = await Contract.filter(id=seed_contract.id).first()
    assert deleted_contract is None


@pytest.mark.asyncio
async def test_get_contracts(
    test_app: AsyncClient, jwt_token_admin, seed_contract: Contract
):
    """Тест получения списка контрактов с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get("/api/contracts/all", headers=headers)

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    response_data = response.json()
    contracts = response_data.get("contracts")
    assert response_data.get("total") >= 1
    assert isinstance(contracts, list)
    assert any(
        contract["contract_id"] == str(seed_contract.id) for contract in contracts
    )
