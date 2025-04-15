import pytest
from httpx import AsyncClient
from app.database.models import Permissions


@pytest.mark.asyncio
async def test_add_permission(test_app: AsyncClient, jwt_token_user):
    """Тест добавления нового разрешения."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    data = {
        "permission_id": 'test_permission',
        "permission_name": 'Тестовое разрешение',
        "comment": "Test permission"
    }

    response = test_app.post("/api/permissions/add",
                             headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    permission = await Permissions.filter(permission_id=data["permission_id"]).first()

    assert permission is not None, "Разрешение не было сохранено в БД"
    assert response_data["permission_id"] == str(permission.permission_id)


@pytest.mark.asyncio
async def test_edit_permission(test_app: AsyncClient, jwt_token_user, seed_permission):
    """Тест редактирования разрешения."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    data = {
        "comment": "Updated comment"
    }

    response = test_app.patch(
        f"/api/permissions/{seed_permission['permission_id']}",
        headers=headers,
        json=data
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    permission = await Permissions.filter(permission_id=seed_permission['permission_id']).first()

    assert permission is not None, "Разрешение не найдено в БД"
    assert response_data["permission_id"] == str(permission.permission_id)
    assert permission.comment == "Updated comment"


@pytest.mark.asyncio
async def test_view_permission(test_app: AsyncClient, jwt_token_user, seed_permission):
    """Тест просмотра разрешения по ID."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get(
        f"/api/permissions/{seed_permission['permission_id']}",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"
    response_data = response.json()

    assert response_data["permission_id"] == str(
        seed_permission["permission_id"])


@pytest.mark.asyncio
async def test_delete_permission(test_app: AsyncClient, jwt_token_user, seed_permission):
    """Тест удаления разрешения."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.delete(
        f"/api/permissions/{seed_permission['permission_id']}",
        headers=headers
    )

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    permission = await Permissions.filter(permission_id=seed_permission['permission_id']).first()
    assert permission is None, "Разрешение не было удалено из базы"


@pytest.mark.asyncio
async def test_get_permissions(test_app: AsyncClient, jwt_token_user, seed_permission):
    """Тест получения списка разрешений с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get(
        "/api/permissions/all",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    permissions = response_data.get('permissions')
    assert isinstance(permissions, list), "Ответ должен быть списком"
    assert response_data.get('total') > 0

    permission_ids = [perm["permission_id"] for perm in permissions]
    assert str(seed_permission["permission_id"]
               ) in permission_ids, "Разрешение отсутствует в списке"
