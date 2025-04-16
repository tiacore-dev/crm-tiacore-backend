import pytest
from httpx import AsyncClient
from app.database.models import LegalEntityType, UserRole, ContractStatus


@pytest.fixture
async def seed_test_data():
    """Создаем тестовые данные перед запуском тестов."""
    await LegalEntityType.create(legal_entity_type_id="adc", entity_name="Компания ABC")
    await LegalEntityType.create(legal_entity_type_id="xyz", entity_name="Компания XYZ")
    await UserRole.create(role_name="Администратор")
    await UserRole.create(role_name="Менеджер")
    await ContractStatus.create(contract_status_id="active", status_name="Активен")
    await ContractStatus.create(contract_status_id="waiting", status_name="Ожидание")

    yield  # После тестов можно добавить `await LegalEntityType.all().delete()`


@pytest.mark.asyncio
async def test_get_legal_entity_types(seed_test_data, test_app: AsyncClient, jwt_token_user):
    """Тест получения всех типов юр. лиц."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    response = test_app.get("/api/legal-entity-types/all", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert {item["entity_name"] for item in data["legal_entity_types"]} == {
        "Компания ABC", "Компания XYZ"}


@pytest.mark.asyncio
async def test_filter_legal_entity_types(seed_test_data, test_app: AsyncClient, jwt_token_user):
    """Тест поиска типов юр. лиц по части имени (LIKE)."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    response = test_app.get(
        "/api/legal-entity-types/all?search=Комп", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert {item["entity_name"] for item in data["legal_entity_types"]} == {
        "Компания ABC", "Компания XYZ"}

    response = test_app.get(
        "/api/legal-entity-types/all?search=ABC", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["legal_entity_types"][0]["entity_name"] == "Компания ABC"


@pytest.mark.asyncio
async def test_pagination_legal_entity_types(seed_test_data, test_app: AsyncClient, jwt_token_user):
    """Тест пагинации списка юр. лиц."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    response = test_app.get(
        "/api/legal-entity-types/all?page=1&page_size=1", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2  # Всего 2 записи
    assert len(data["legal_entity_types"]) == 1  # Вернули 1 запись

    response_page_2 = test_app.get(
        "/api/legal-entity-types/all?page=2&page_size=1", headers=headers)
    assert response_page_2.status_code == 200
    # Вторая страница тоже с 1 записью
    assert len(response_page_2.json()["legal_entity_types"]) == 1


@pytest.mark.asyncio
async def test_sorting_legal_entity_types(seed_test_data, test_app: AsyncClient, jwt_token_user):
    """Тест сортировки типов юр. лиц."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get(
        "/api/legal-entity-types/all?sort_by=entity_name&order=asc", headers=headers)
    assert response.status_code == 200
    data_asc = response.json()
    names_asc = [item["entity_name"]
                 for item in data_asc["legal_entity_types"]]

    response_desc = test_app.get(
        "/api/legal-entity-types/all?sort_by=entity_name&order=desc", headers=headers)
    assert response_desc.status_code == 200
    data_desc = response_desc.json()
    names_desc = [item["entity_name"]
                  for item in data_desc["legal_entity_types"]]

    # 🔥 Проверяем, что порядок действительно изменился
    assert names_asc == sorted(
        names_asc), "ASC сортировка работает неправильно"
    assert names_desc == sorted(
        names_asc, reverse=True), "DESC сортировка работает неправильно"


@pytest.mark.asyncio
async def test_get_contract_statuses(seed_test_data, test_app: AsyncClient, jwt_token_user):
    """Тест получения всех статусов контрактов."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    response = test_app.get("/api/contract-statuses/all", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert {item["status_name"]
            for item in data["contract_statuses"]} == {"Активен", "Ожидание"}
