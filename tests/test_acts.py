import pytest
from httpx import AsyncClient
from app.database.models import Acts


@pytest.mark.asyncio
async def test_add_act(test_app: AsyncClient, jwt_token_admin, seed_contract, seed_company):
    """Тест добавления нового акта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "act_number": "ACT-001",
        "act_date": 1700000000,  # Пример UNIX timestamp
        "contract": seed_contract["contract_id"],
        "company": seed_company['company_id']
    }

    response = test_app.post("/api/acts/add", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    data = response.json()
    act = await Acts.filter(act_number="ACT-001").first()
    assert act is not None, "Акт не найден в базе"
    assert data["act_id"] == str(act.act_id)


@pytest.mark.asyncio
async def test_edit_act(test_app: AsyncClient, jwt_token_admin, seed_act):
    """Тест редактирования акта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "act_number": "Updated ACT-001",
        "act_date": 1800000000  # Новый timestamp
    }

    response = test_app.patch(
        f"/api/acts/{seed_act['act_id']}",
        headers=headers,
        json=data
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что данные обновились в БД
    updated_act = await Acts.filter(act_id=seed_act["act_id"]).first()
    assert updated_act is not None
    assert updated_act.act_number == "Updated ACT-001"
    assert updated_act.act_date == 1800000000


@pytest.mark.asyncio
async def test_view_act(test_app: AsyncClient, jwt_token_admin, seed_act):
    """Тест просмотра информации об акте."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.get(
        f"/api/acts/{seed_act['act_id']}",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert response_data["act_id"] == str(seed_act["act_id"])
    assert response_data["act_number"] == seed_act["act_number"]
    assert response_data["act_date"] == seed_act["act_date"]


@pytest.mark.asyncio
async def test_delete_act(test_app: AsyncClient, jwt_token_admin, seed_act):
    """Тест удаления акта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.delete(
        f"/api/acts/{seed_act['act_id']}",
        headers=headers
    )

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что акт удалён
    deleted_act = await Acts.filter(act_id=seed_act["act_id"]).first()
    assert deleted_act is None


@pytest.mark.asyncio
async def test_get_acts(test_app: AsyncClient, jwt_token_admin, seed_act):
    """Тест получения списка актов с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.get(
        "/api/acts/all",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    acts = response_data.get('acts')
    assert response_data.get('total') >= 1
    assert isinstance(acts, list)
    assert any(act["act_id"] == seed_act["act_id"] for act in acts)
