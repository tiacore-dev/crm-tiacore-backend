import pytest
from httpx import AsyncClient
from app.database.models import Contract


@pytest.mark.asyncio
async def test_add_contract(
    test_app: AsyncClient,
    jwt_token_user,
    seed_legal_entity,
    seed_legal_entity_buyer,
    seed_contract_status
):
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    form_data = {
        "contract_name": "Test Contract",
        "contract_date": "1710000000",
        "buyer": str(seed_legal_entity["legal_entity_id"]),
        "seller": str(seed_legal_entity_buyer["legal_entity_id"]),
        "comment": "Test contract comment",
        "status": str(seed_contract_status["contract_status_id"]),
    }

    response = test_app.post(
        "/api/contracts/add",
        data=form_data,
        headers={
            **headers,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    data = response.json()
    contract = await Contract.filter(contract_name="Test Contract").first()
    assert data["contract_id"] == str(contract.contract_id)


@pytest.mark.asyncio
async def test_edit_contract(
    test_app: AsyncClient,
    jwt_token_user,
    seed_contract,
    seed_contract_status_updated
):
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    form_data = {
        "contract_name": "Updated Contract Name",
        "comment": "Updated comment",
        "status": str(seed_contract_status_updated["contract_status_id"]),
    }

    response = test_app.patch(
        f"/api/contracts/{seed_contract['contract_id']}",
        data=form_data,
        headers={
            **headers,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    updated_contract = await Contract.filter(contract_id=seed_contract["contract_id"]).first().prefetch_related("status")

    assert updated_contract.contract_name == "Updated Contract Name"
    assert updated_contract.comment == "Updated comment"
    assert updated_contract.status.contract_status_id == seed_contract_status_updated[
        "contract_status_id"]


@pytest.mark.asyncio
async def test_view_contract(test_app: AsyncClient, jwt_token_user, seed_contract):
    """Тест просмотра информации о контракте."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get(
        f"/api/contracts/{seed_contract['contract_id']}",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert response_data["contract_id"] == str(seed_contract["contract_id"])
    assert response_data["contract_name"] == seed_contract["contract_name"]


@pytest.mark.asyncio
async def test_delete_contract(test_app: AsyncClient, jwt_token_user, seed_contract):
    """Тест удаления контракта."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.delete(
        f"/api/contracts/{seed_contract['contract_id']}",
        headers=headers
    )

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что контракт удалён
    deleted_contract = await Contract.filter(contract_id=seed_contract["contract_id"]).first()
    assert deleted_contract is None


@pytest.mark.asyncio
async def test_get_contracts(test_app: AsyncClient, jwt_token_user, seed_contract):
    """Тест получения списка контрактов с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get(
        "/api/contracts/all",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    contracts = response_data.get('contracts')
    assert response_data.get('total') >= 1
    assert isinstance(contracts, list)
    assert any(contract["contract_id"] == seed_contract["contract_id"]
               for contract in contracts)
