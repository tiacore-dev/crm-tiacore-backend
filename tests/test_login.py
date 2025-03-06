import json
import pytest


@pytest.mark.asyncio
async def test_protected_endpoint(test_app, jwt_token_user):
    """Проверяем доступ к защищенному эндпоинту."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    response = test_app.get("/api/auth/protected", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Доступ разрешён"


@pytest.mark.usefixtures("seed_user")
@pytest.mark.asyncio
async def test_login_success(test_app):
    """Проверяем успешную аутентификацию."""
    response = test_app.post(
        "/api/auth/token",
        json={"username": "test_user", "password": "qweasdzcx"}
    )

    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert "refresh_token" in json_data


@pytest.mark.asyncio
async def test_refresh_token_success(test_app, jwt_token_user):
    """Проверяем, что refresh-токен можно обменять на новый access-токен."""
    response = test_app.post(
        "/api/auth/refresh", data=json.dumps({"refresh_token": jwt_token_user["refresh_token"]}))

    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert "refresh_token" in json_data


@pytest.mark.asyncio
async def test_login_failure(test_app):
    """Проверяем неудачную аутентификацию с неправильным паролем."""
    response = test_app.post(
        "/api/auth/token",
        json={"username": "test_user", "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверные учетные данные"


@pytest.mark.asyncio
async def test_refresh_token_invalid(test_app):
    """Проверяем обновление токена с неверным refresh-токеном."""
    response = test_app.post(
        "/api/auth/refresh", data=json.dumps({"refresh_token": "invalid_token"}))

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный или просроченный токен"
