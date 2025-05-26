import pytest
from httpx import AsyncClient

from app.database.models import LegalEntity


@pytest.mark.asyncio
async def test_add_legal_entity(
    test_app: AsyncClient, jwt_token_admin, seed_company, seed_legal_entity_type
):
    """Тест добавления нового юридического лица."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "legal_entity_name": "Test Legal Entity",
        "inn": "123456789012",
        "kpp": "123456789",
        "vat_rate": 20,
        "address": "Test Address",
        "entity_type": seed_legal_entity_type["legal_entity_type_id"],
        "signer": "Test Signer",
        "company": seed_company["company_id"],
        "relation_type": "seller",
    }

    response = await test_app.post(
        f"/api/legal-entities/add?company={seed_company['company_id']}",
        headers=headers,
        json=data,
    )
    assert response.status_code == 201, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    data = response.json()
    legal_entity = await LegalEntity.filter(
        legal_entity_name="Test Legal Entity"
    ).first()
    if legal_entity:
        assert data["legal_entity_id"] == str(legal_entity.legal_entity_id)


@pytest.mark.asyncio
async def test_edit_legal_entity(
    test_app: AsyncClient, jwt_token_admin, seed_legal_entity, seed_company
):
    """Тест редактирования юридического лица."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "legal_entity_name": "Updated Legal Entity Name",
        "description": "Обновленное описание",
        "address": "Updated Address",
    }

    response = await test_app.patch(
        f"/api/legal-entities/{seed_legal_entity['legal_entity_id']}?company={seed_company['company_id']}",
        headers=headers,
        json=data,
    )

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    # Проверяем, что данные обновились в БД
    updated_legal_entity = await LegalEntity.filter(
        legal_entity_id=seed_legal_entity["legal_entity_id"]
    ).first()
    assert updated_legal_entity is not None
    assert updated_legal_entity.legal_entity_name == "Updated Legal Entity Name"
    assert updated_legal_entity.address == "Updated Address"


@pytest.mark.asyncio
async def test_view_legal_entity(
    test_app: AsyncClient, jwt_token_admin, seed_legal_entity
):
    """Тест просмотра информации о юридическом лице."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get(
        f"/api/legal-entities/{seed_legal_entity['legal_entity_id']}", headers=headers
    )

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    response_data = response.json()
    assert response_data["legal_entity_id"] == str(seed_legal_entity["legal_entity_id"])
    assert response_data["legal_entity_name"] == seed_legal_entity["legal_entity_name"]
    assert response_data["address"] == seed_legal_entity["address"]


@pytest.mark.asyncio
async def test_delete_legal_entity(
    test_app: AsyncClient, jwt_token_admin, seed_legal_entity, seed_company
):
    """Тест удаления юридического лица."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.delete(
        f"/api/legal-entities/{seed_legal_entity['legal_entity_id']}?company={seed_company['company_id']}",
        headers=headers,
    )

    assert response.status_code == 204, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    # Проверяем, что юридическое лицо удалено
    deleted_legal_entity = await LegalEntity.filter(
        legal_entity_id=seed_legal_entity["legal_entity_id"]
    ).first()
    assert deleted_legal_entity is None


@pytest.mark.asyncio
async def test_get_legal_entities(
    test_app: AsyncClient, jwt_token_admin, seed_legal_entity
):
    """Тест получения списка юридических лиц с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get("/api/legal-entities/all", headers=headers)

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    response_data = response.json()
    assert response_data.get("total") >= 1
    entities = response_data.get("entities")
    assert isinstance(entities, list)
    assert any(
        entity["legal_entity_id"] == seed_legal_entity["legal_entity_id"]
        for entity in entities
    )
