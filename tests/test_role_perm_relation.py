import pytest
from httpx import AsyncClient
from app.database.models import RolePermissionRelation


@pytest.mark.asyncio
async def test_add_role_permission_relation(test_app: AsyncClient, jwt_token_admin, seed_role_admin, seed_permission):
    """Проверка создания связи роли и разрешения"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    data = {
        "role": seed_role_admin["role_id"],
        "permission": seed_permission["permission_id"]
    }

    response = test_app.post(
        "/api/role-permission-relations/add", headers=headers, json=data
    )
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert "role_permission_id" in response_data, "Не возвращается role_permission_id!"

    relation = await RolePermissionRelation.filter(role_permission_id=response_data["role_permission_id"]).first()
    assert relation is not None, "Связь не сохранена в БД!"


@pytest.mark.asyncio
async def test_get_role_permission_relation(test_app: AsyncClient, jwt_token_admin, seed_role_permission_relation):
    """Проверка просмотра одной связи"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.get(
        f"/api/role-permission-relations/{seed_role_permission_relation['role_permission_id']}", headers=headers
    )
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"
    assert response.json()[
        "role_permission_id"] == seed_role_permission_relation["role_permission_id"]


@pytest.mark.asyncio
async def test_update_role_permission_relation(
    test_app: AsyncClient,
    jwt_token_admin,
    seed_role_permission_relation,
    seed_role_manager,
):
    """Проверка изменения роли у связи"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    update_data = {"role": seed_role_manager["role_id"]}

    response = test_app.patch(
        f"/api/role-permission-relations/{seed_role_permission_relation['role_permission_id']}",
        headers=headers,
        json=update_data
    )
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert "role_permission_id" in response_data
    assert response_data["role_permission_id"] == seed_role_permission_relation["role_permission_id"]

    # ✅ Проверяем в БД
    relation = await RolePermissionRelation.filter(
        role_permission_id=seed_role_permission_relation["role_permission_id"]
    ).prefetch_related("role").first()

    assert relation is not None
    assert str(relation.role.role_id) == seed_role_manager["role_id"]


@pytest.mark.asyncio
async def test_delete_role_permission_relation(test_app: AsyncClient, jwt_token_admin, seed_role_permission_relation):
    """Проверка удаления связи"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.delete(
        f"/api/role-permission-relations/{seed_role_permission_relation['role_permission_id']}", headers=headers
    )
    assert response.status_code == 204, f"Ошибка удаления: {response.status_code}, {response.text}"

    relation = await RolePermissionRelation.filter(role_permission_id=seed_role_permission_relation["role_permission_id"]).first()
    assert relation is None, "Связь не была удалена из БД!"


@pytest.mark.asyncio
async def test_get_all_role_permission_relations(test_app: AsyncClient, jwt_token_admin, seed_role_permission_relation):
    """Проверка получения всех связей"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.get(
        "/api/role-permission-relations/all", headers=headers)
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    relations = response_data.get("relations")
    assert isinstance(relations, list), "Ответ должен быть списком!"
    assert response_data.get("total") >= 1
