import pytest
from httpx import AsyncClient
from app.database.models import User, UserCompanyRelation


@pytest.mark.asyncio
async def test_add_user(test_app: AsyncClient, jwt_token_admin, seed_company, other_role):
    """Тест добавления нового пользователя."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "username": "testuser",
        "full_name": "Test User",
        "position": "Developer",
        "password": "securepassword123"
    }

    response = test_app.post(
        f"/api/users/add?company={seed_company['company_id']}", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что пользователь добавлен в базу
    response_data = response.json()
    user = await User.filter(username="testuser").first()
    relation = await UserCompanyRelation.filter(user=user).prefetch_related("company").first()

    assert user is not None, "Пользователь не был сохранён в БД"
    assert response_data["user_id"] == str(user.user_id)
    assert str(relation.company.company_id) == seed_company['company_id']


@pytest.mark.asyncio
async def test_edit_user(test_app: AsyncClient, jwt_token_admin, seed_user, seed_company):
    """Тест редактирования пользователя."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "full_name": "Updated User",
        "position": "Senior Developer"
    }

    response = test_app.patch(
        f"/api/users/{seed_user['user_id']}?company={seed_company['company_id']}",
        headers=headers,
        json=data
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что пользователь обновился в базе
    response_data = response.json()
    user = await User.filter(user_id=seed_user["user_id"]).first()

    assert user is not None, "Пользователь не найден в базе"
    assert response_data["user_id"] == str(user.user_id)
    assert user.full_name == "Updated User"
    assert user.position == "Senior Developer"


@pytest.mark.asyncio
async def test_view_user(test_app: AsyncClient, jwt_token_admin, seed_user):
    """Тест просмотра пользователя по ID."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.get(
        f"/api/users/{seed_user['user_id']}",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    print(response_data)  # Посмотрим, какие поля реально пришли

    assert response_data["user_id"] == str(seed_user["user_id"])
    assert response_data["username"] == seed_user["username"]
    assert response_data["full_name"] == seed_user["full_name"]


@pytest.mark.asyncio
async def test_delete_user(test_app: AsyncClient, jwt_token_admin, seed_user, seed_company):
    """Тест удаления пользователя."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.delete(
        f"/api/users/{seed_user['user_id']}?company={seed_company['company_id']}",
        headers=headers
    )

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что пользователь больше не существует в базе
    user = await User.filter(user_id=seed_user["user_id"]).first()
    assert user is None, "Пользователь не был удалён из базы"


@pytest.mark.asyncio
async def test_get_users(test_app: AsyncClient, jwt_token_admin, seed_user):
    """Тест получения списка пользователей с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.get(
        "/api/users/all",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    users = response_data.get('users')
    assert isinstance(users, list), "Ответ должен быть списком"

    # Проверяем, что в списке есть наш тестовый пользователь
    user_ids = [user["user_id"] for user in users]
    assert str(
        seed_user["user_id"]) in user_ids, "Тестовый пользователь отсутствует в списке"
