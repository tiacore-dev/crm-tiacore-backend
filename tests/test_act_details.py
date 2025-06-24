import pytest
from httpx import AsyncClient

from app.database.models import ActDetails, Acts, Service


@pytest.mark.asyncio
async def test_add_act_detail(
    test_app: AsyncClient, jwt_token_admin, seed_act: Acts, seed_service: Service
):
    """Тест добавления новой детали акта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "act": str(seed_act.id),
        "service": str(seed_service.id),
        "quantity": "5.500",
        # "summ": "1000.50",
        "price": "20",
    }

    response = await test_app.post("/api/act-details/add", headers=headers, json=data)
    assert response.status_code == 201, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    data = response.json()
    act_detail = await ActDetails.filter(act_id=seed_act.id).first()
    assert act_detail is not None, "Деталь акта не найдена в базе"
    assert data["act_detail_id"] == str(act_detail.id)


@pytest.mark.asyncio
async def test_edit_act_detail(
    test_app: AsyncClient, jwt_token_admin, seed_act_detail: ActDetails
):
    """Тест редактирования детали акта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "quantity": "10.250",
    }

    response = await test_app.patch(
        f"/api/act-details/{seed_act_detail.id}",
        headers=headers,
        json=data,
    )

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    # Проверяем, что данные обновились в БД
    updated_act_detail = await ActDetails.filter(id=seed_act_detail.id).first()
    assert updated_act_detail is not None
    assert updated_act_detail.quantity == 10.250


@pytest.mark.asyncio
async def test_view_act_detail(
    test_app: AsyncClient, jwt_token_admin, seed_act_detail: ActDetails
):
    """Тест просмотра информации о детали акта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get(
        f"/api/act-details/{seed_act_detail.id}", headers=headers
    )

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    response_data = response.json()
    assert response_data["act_detail_id"] == str(seed_act_detail.id)


@pytest.mark.asyncio
async def test_delete_act_detail(
    test_app: AsyncClient, jwt_token_admin, seed_act_detail: ActDetails
):
    """Тест удаления детали акта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    # Дебаг, проверяем есть ли запись перед удалением
    act_detail = await ActDetails.filter(id=seed_act_detail.id).first()
    assert act_detail is not None, (
        "Ошибка: act_detail не существует в БД перед удалением"
    )

    response = await test_app.delete(
        f"/api/act-details/{seed_act_detail.id}", headers=headers
    )

    assert response.status_code == 204, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    # Проверяем, что юридическое лицо удалено
    deleted_act_detail = await ActDetails.filter(id=seed_act_detail.id).first()
    assert deleted_act_detail is None, "Ошибка: act_detail не удалена"


@pytest.mark.asyncio
async def test_get_all_act_details(
    test_app: AsyncClient, jwt_token_admin, seed_act_detail: ActDetails
):
    """Тест получения списка деталей акта с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get("/api/act-details/all", headers=headers)

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    response_data = response.json()
    act_details = response_data.get("act_details")
    assert response_data.get("total") >= 1
    assert isinstance(act_details, list), "Ответ должен быть списком!"
    assert any(
        detail["act_detail_id"] == str(seed_act_detail.id) for detail in act_details
    ), "Тестовая деталь акта не найдена в списке!"
