import pytest
from httpx import AsyncClient
from app.database.models import LegalEntityType, UserRole, ContractStatus


@pytest.fixture
async def seed_test_data():
    """Создаем тестовые данные перед запуском тестов."""
    await LegalEntityType.create(legal_entity_type_id="adc", entity_name="Компания ABC")
    await LegalEntityType.create(legal_entity_type_id="xyz", entity_name="Компания XYZ")
    await UserRole.create(role_id="admin", role_name="Администратор")
    await UserRole.create(role_id="manager", role_name="Менеджер")
    await ContractStatus.create(contract_status_id="active", status_name="Активен")
    await ContractStatus.create(contract_status_id="waiting", status_name="Ожидание")

    yield  # После тестов можно добавить `await LegalEntityType.all().delete()`


@pytest.mark.asyncio
async def test_get_legal_entity_types(seed_test_data, test_app: AsyncClient):
    """Тест получения всех типов юр. лиц."""
    response = test_app.get("/api/get-all/legal-entity-types/")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert data["items"][0]["name"] in ["Компания ABC", "Компания XYZ"]


@pytest.mark.asyncio
async def test_get_user_roles(seed_test_data, test_app: AsyncClient):
    """Тест получения всех ролей пользователей."""
    response = test_app.get("/api/get-all/user-roles/")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert {item["name"]
            for item in data["items"]} == {"Администратор", "Менеджер"}


@pytest.mark.asyncio
async def test_get_contract_statuses(seed_test_data, test_app: AsyncClient):
    """Тест получения всех статусов контрактов."""
    response = test_app.get("/api/get-all/contract-statuses/")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert {item["name"] for item in data["items"]} == {"Активен", "Ожидание"}


@pytest.mark.asyncio
async def test_filter_like_legal_entity_types(seed_test_data, test_app: AsyncClient):
    """Тест поиска LIKE (должен находить по части имени)."""
    response = test_app.get("/api/get-all/legal-entity-types/?search=Комп")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2  # Должны найти обе компании
    assert {item["name"]
            for item in data["items"]} == {"Компания ABC", "Компания XYZ"}

    response = test_app.get("/api/get-all/legal-entity-types/?search=ABC")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Компания ABC"


@pytest.mark.asyncio
async def test_pagination_legal_entity_types(seed_test_data, test_app: AsyncClient):
    """Тест пагинации."""
    response = test_app.get(
        "/api/get-all/legal-entity-types/?page=1&page_size=1")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2  # Всего 2 записи
    assert len(data["items"]) == 1  # Должен вернуть только одну запись

    response_page_2 = test_app.get(
        "/api/get-all/legal-entity-types/?page=2&page_size=1")
    assert response_page_2.status_code == 200
    # Вторая страница тоже с одной записью
    assert len(response_page_2.json()["items"]) == 1


@pytest.mark.asyncio
async def test_sorting_legal_entity_types(seed_test_data, test_app: AsyncClient):
    """Тест сортировки."""
    response = test_app.get(
        "/api/get-all/legal-entity-types/?sort_by=name&order=asc")
    assert response.status_code == 200

    data = response.json()
    # Проверяем сортировку по имени
    assert data["items"][0]["name"] == "Компания ABC"

    response_desc = test_app.get(
        "/api/get-all/legal-entity-types/?sort_by=name&order=desc")
    assert response_desc.status_code == 200
    # Проверяем сортировку по убыванию
    assert response_desc.json()["items"][0]["name"] == "Компания XYZ"
