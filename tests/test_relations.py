import pytest
from httpx import AsyncClient
from app.database.models import UserCompanyRelation


@pytest.mark.asyncio
async def test_add_user_company_relation(test_app: AsyncClient, jwt_token_user, seed_user, seed_company, seed_role):
    """Проверка создания связи пользователя и компании"""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    data = {
        "user": seed_user['user_id'],
        "company": seed_company['company_id'],
        "role": seed_role['role_id'],
    }

    response = test_app.post(
        "/api/user-company-relations/add", headers=headers, json=data)
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert "user_company_id" in response_data, "Не возвращается user_company_id!"

    relation = await UserCompanyRelation.filter(user_company_id=response_data["user_company_id"]).first()
    assert relation is not None, "Связь не сохранена в БД!"


@pytest.mark.asyncio
async def test_get_user_company_relation(test_app: AsyncClient, jwt_token_user, seed_relation):
    """Проверка просмотра одной связи"""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get(
        f"/api/user-company-relations/{seed_relation["user_company_id"]}", headers=headers)
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"
    assert response.json()[
        "user_company_id"] == seed_relation["user_company_id"]


@pytest.mark.asyncio
async def test_update_user_company_relation(test_app: AsyncClient, jwt_token_user, seed_relation, seed_role_manager):
    """Проверка изменения связи"""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    update_data = {"role": "manager"}
    response = test_app.patch(
        f"/api/user-company-relations/{seed_relation['user_company_id']}", headers=headers, json=update_data)
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что только ID вернулся
    response_data = response.json()
    assert "user_company_id" in response_data, "В ответе нет user_company_id"
    assert response_data["user_company_id"] == seed_relation["user_company_id"]

    # Проверяем в БД, загружая связанные данные
    relation = await UserCompanyRelation.filter(user_company_id=seed_relation["user_company_id"]).prefetch_related("role").first()
    assert relation is not None, "Связь не найдена в БД!"
    assert relation.role.role_id == "manager", f"Роль не обновилась в БД! Ожидали 'manager', а получили '{relation.role.role_id}'"


@pytest.mark.asyncio
async def test_delete_user_company_relation(test_app: AsyncClient, jwt_token_user, seed_relation):
    """Проверка удаления связи"""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.delete(
        f"/api/user-company-relations/{seed_relation["user_company_id"]}", headers=headers)
    assert response.status_code == 200, f"Ошибка удаления: {response.status_code}, {response.text}"

    # Проверяем, что связь действительно удалена
    relation = await UserCompanyRelation.filter(user_company_id=seed_relation["user_company_id"]).first()
    assert relation is None, "Связь не была удалена из БД!"


@pytest.mark.asyncio
async def test_get_all_user_company_relations(test_app: AsyncClient, jwt_token_user, seed_relation):
    """Проверка получения всех связей"""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get("/api/user-company-relations/all", headers=headers)
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert isinstance(response_data, list), "Ответ должен быть списком!"
    assert len(response_data) >= 1
