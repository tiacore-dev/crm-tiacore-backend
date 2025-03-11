import pytest
from httpx import AsyncClient
from app.database.models import Service


@pytest.mark.asyncio
async def test_add_service(test_app: AsyncClient, jwt_token_user):
    """Тест добавления новой услуги."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    data = {
        "service_name": "Test Service"
    }

    response = test_app.post("/api/services/add", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что услуга добавлена в базу
    response_data = response.json()
    service = await Service.filter(service_name="Test Service").first()

    assert service is not None, "Услуга не была сохранена в БД"
    assert response_data["service_id"] == str(service.service_id)


@pytest.mark.asyncio
async def test_edit_service(test_app: AsyncClient, jwt_token_user, seed_service):
    """Тест редактирования услуги."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    data = {
        "service_name": "New name"
    }

    response = test_app.patch(
        f"/api/services/{seed_service['service_id']}",
        headers=headers,
        json=data
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что услуга обновилась в базе
    response_data = response.json()
    service = await Service.filter(service_id=seed_service['service_id']).first()

    assert service is not None, "Услуга не найдена в базе"
    assert response_data["service_id"] == str(service.service_id)
    assert service.service_name == "New name"


@pytest.mark.asyncio
async def test_view_service(test_app: AsyncClient, jwt_token_user, seed_service):
    """Тест просмотра услуги по ID."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get(
        f"/api/services/{seed_service['service_id']}",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert response_data["service_id"] == str(seed_service["service_id"])
    assert response_data["service_name"] == seed_service["service_name"]


@pytest.mark.asyncio
async def test_delete_service(test_app: AsyncClient, jwt_token_user, seed_service):
    """Тест удаления услуги."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.delete(
        f"/api/services/{seed_service['service_id']}",
        headers=headers
    )

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что услуга больше не существует в базе
    service = await Service.filter(service_id=seed_service['service_id']).first()
    assert service is None, "Услуга не была удалена из базы"


@pytest.mark.asyncio
async def test_get_services(test_app: AsyncClient, jwt_token_user, seed_service):
    """Тест получения списка услуг с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get(
        "/api/services/all",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert isinstance(response_data, list), "Ответ должен быть списком"

    # Проверяем, что в списке есть наша тестовая услуга
    service_ids = [service["service_id"] for service in response_data]
    assert str(seed_service["service_id"]
               ) in service_ids, "Тестовая услуга отсутствует в списке"
