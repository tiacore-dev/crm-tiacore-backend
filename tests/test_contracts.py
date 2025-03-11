import pytest
from httpx import AsyncClient
from app.database.models import Contract


@pytest.mark.asyncio
async def test_add_contract(test_app: AsyncClient, jwt_token_user, seed_legal_entity, seed_legal_entity_buyer, seed_contract_status):
    """Тест добавления нового контракта."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    data = {
        "contract_name": "Test Contract",
        "contract_date": 1710000000,  # UNIX timestamp
        "buyer": seed_legal_entity["legal_entity_id"],
        "seller": seed_legal_entity_buyer["legal_entity_id"],
        "comment": "Test contract comment",
        "file": "http://example.com/contract.pdf",
        "status": seed_contract_status["contract_status_id"]
    }

    response = test_app.post("/api/contracts/add", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    data = response.json()
    contract = await Contract.filter(contract_name="Test Contract").first()
    assert data["contract_id"] == str(contract.contract_id)


@pytest.mark.asyncio
async def test_edit_contract(test_app: AsyncClient, jwt_token_user, seed_contract, seed_contract_status_updated):
    """Тест редактирования контракта."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    data = {
        "contract_name": "Updated Contract Name",
        "comment": "Updated comment",
        "file": "http://example.com/updated_contract.pdf",
        "status": seed_contract_status_updated["contract_status_id"]
    }

    response = test_app.patch(
        f"/api/contracts/{seed_contract['contract_id']}",
        headers=headers,
        json=data
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    # Загружаем контракт вместе с его статусом (fetch_related)
    updated_contract = await Contract.filter(contract_id=seed_contract["contract_id"]).first().prefetch_related("status")

    assert updated_contract is not None
    assert updated_contract.contract_name == "Updated Contract Name"
    assert updated_contract.comment == "Updated comment"
    assert updated_contract.file == "http://example.com/updated_contract.pdf"
    assert updated_contract.status is not None, "Статус контракта не загружен!"
    assert updated_contract.status.contract_status_id == seed_contract_status_updated["contract_status_id"], \
        f"Ожидали {seed_contract_status_updated['contract_status_id']}, а получили {updated_contract.status.contract_status_id}"


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
    assert response_data["file"] == seed_contract["file"]


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
    assert isinstance(response_data, list)
    assert any(contract["contract_id"] == seed_contract["contract_id"]
               for contract in response_data)
