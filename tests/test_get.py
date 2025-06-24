import pytest
from httpx import AsyncClient

from app.database.models import ContractStatus


@pytest.fixture
async def seed_test_data():
    await ContractStatus.create(id="active", name="Активен")
    await ContractStatus.create(id="waiting", name="Ожидание")

    yield  # После тестов можно добавить `await LegalEntityType.all().delete()`


@pytest.mark.asyncio
async def test_get_contract_statuses(
    seed_test_data, test_app: AsyncClient, jwt_token_admin
):
    """Тест получения всех статусов контрактов."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    response = await test_app.get("/api/contract-statuses/all", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert {item["status_name"] for item in data["contract_statuses"]} == {
        "Активен",
        "Ожидание",
    }
