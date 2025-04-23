import pytest
from httpx import AsyncClient
from app.database.models import EntityCompanyRelation


@pytest.mark.asyncio
async def test_add_entity_company_relation(test_app: AsyncClient, jwt_token_admin, seed_company, seed_legal_entity):
    """Проверка создания связи компании и юрлица"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    data = {
        "company": seed_company["company_id"],
        "legal_entity": seed_legal_entity["legal_entity_id"],
        "relation_type": "buyer"
    }

    response = test_app.post(
        "/api/entity-company-relations/add", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert "entity_company_relation_id" in response_data

    relation = await EntityCompanyRelation.filter(entity_company_relation_id=response_data["entity_company_relation_id"]).first()
    assert relation is not None


@pytest.mark.asyncio
async def test_get_entity_company_relation(test_app: AsyncClient, jwt_token_admin, seed_entity_relation):
    """Проверка просмотра одной связи"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.get(
        f"/api/entity-company-relations/{seed_entity_relation['entity_company_relation_id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()[
        "entity_company_relation_id"] == seed_entity_relation["entity_company_relation_id"]


@pytest.mark.asyncio
async def test_update_entity_company_relation(test_app: AsyncClient, jwt_token_admin, seed_entity_relation):
    """Проверка изменения связи (добавим описание)"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    update_data = {"description": "Описание связи"}
    response = test_app.patch(
        f"/api/entity-company-relations/{seed_entity_relation['entity_company_relation_id']}", headers=headers, json=update_data)
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["entity_company_relation_id"] == seed_entity_relation["entity_company_relation_id"]

    relation = await EntityCompanyRelation.get(entity_company_relation_id=response_data["entity_company_relation_id"])
    assert relation.description == "Описание связи"


@pytest.mark.asyncio
async def test_delete_entity_company_relation(test_app: AsyncClient, jwt_token_admin, seed_entity_relation):
    """Проверка удаления связи"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.delete(
        f"/api/entity-company-relations/{seed_entity_relation['entity_company_relation_id']}", headers=headers)
    assert response.status_code == 204

    relation = await EntityCompanyRelation.filter(entity_company_relation_id=seed_entity_relation["entity_company_relation_id"]).first()
    assert relation is None


@pytest.mark.asyncio
async def test_get_all_entity_company_relations(test_app: AsyncClient, jwt_token_admin, seed_entity_relation):
    """Проверка получения списка связей"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.get(
        "/api/entity-company-relations/all", headers=headers)
    assert response.status_code == 200

    response_data = response.json()
    relations = response_data.get("relations")
    assert isinstance(relations, list)
    assert response_data.get("total") >= 1
