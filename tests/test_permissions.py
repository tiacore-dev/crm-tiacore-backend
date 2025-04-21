import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_permissions(test_app: AsyncClient, jwt_token_admin, seed_permission):
    """Тест получения списка разрешений с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

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
