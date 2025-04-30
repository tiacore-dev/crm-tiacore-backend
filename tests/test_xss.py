import pytest
from httpx import AsyncClient
from app.database.models import Company,  User


@pytest.mark.parametrize("endpoint, model_class, payload_key", [
    ("/api/companies/add", Company, "company_name"),
    ("/api/users/add", User, "email"),
])
@pytest.mark.asyncio
async def test_xss_injection(test_app: AsyncClient, jwt_token_admin, endpoint, model_class, payload_key, seed_company):
    """Проверяем, что API защищено от XSS-атак"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {payload_key: "<script>alert('XSS')</script>"}
    # Если тестируем пользователя, добавляем пароль и имя
    if payload_key == "email":
        data["password"] = "SecurePass123"
        data["full_name"] = "Test User"
        data['company'] = seed_company['company_id']

    response = test_app.post(endpoint, headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    # Получаем ID созданной сущности
    response_data = response.json()
    entity = await model_class.filter(**{f"{model_class.__name__.lower()}_id": response_data[f"{model_class.__name__.lower()}_id"]}).first()

    # Проверяем, что XSS не осталось
    assert "script" not in getattr(
        entity, payload_key), "XSS-инъекция сохранилась в БД!"
    assert "<" not in getattr(entity, payload_key), "HTML-теги остались!"
