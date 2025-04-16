import asyncio
import pytest
from httpx import AsyncClient
from loguru import logger
from app.database.models import Company


@pytest.mark.asyncio
async def test_mass_create_companies(test_app: AsyncClient, jwt_token_admin, seed_company):
    """Создаем 100 компаний подряд и проверяем, не падает ли API"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    for i in range(100):
        data = {"company_name": f"Company {i}"}
        response = test_app.post(f"/api/companies/add?company={seed_company['company_id']}",
                                 headers=headers, json=data)
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_mass_create_companies_async(test_app: AsyncClient, jwt_token_admin, seed_company):
    """Создаем 100 компаний конкурентно"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    async def create_company(i):
        data = {"company_name": f"Company {i}"}
        response = test_app.post(f"/api/companies/add?company={seed_company['company_id']}",
                                 headers=headers, json=data)
        assert response.status_code == 201, f"Ошибка на компании {i}: {response.text}"

    tasks = [create_company(i) for i in range(100)]
    await asyncio.gather(*tasks)


@pytest.mark.parametrize("headers", [
    {"Authorization": ""},  # Пустой токен
    {"Authorization": "Bearer invalidtoken"}  # Неверный токен
])
@pytest.mark.asyncio
async def test_unauthorized_access(test_app: AsyncClient, headers):
    """Проверка, что API отказывает в доступе без авторизации"""
    response = test_app.get("/api/companies/all", headers=headers)
    assert response.status_code == 401, f"Ожидали 401, но получили {response.status_code}"


@pytest.mark.asyncio
async def test_mass_delete_companies(test_app: AsyncClient, jwt_token_admin, seed_company):
    """Создаем 10 компаний, затем удаляем их всех"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    created_ids = []

    # Создаем 10 компаний
    for i in range(10):
        data = {"company_name": f"ToDelete {i}"}
        response = test_app.post(f"/api/companies/add?company={seed_company['company_id']}",
                                 headers=headers, json=data)
        assert response.status_code == 201
        created_ids.append(response.json()["company_id"])
    await asyncio.sleep(0.1)
    # Удаляем компании
    for company_id in created_ids:
        entity = await Company.filter(company_id=company_id).first()
        assert entity is not None, f"Компания {company_id} не найдена перед удалением!"
        logger.info(f"Компания {company_id} найдена перед удалением")

        response = test_app.delete(
            f"/api/companies/{company_id}?company={seed_company['company_id']}", headers=headers)
        assert response.status_code == 204, f"Ошибка при удалении {company_id}"


@pytest.mark.asyncio
async def test_large_data_handling(test_app: AsyncClient, jwt_token_admin, seed_company):
    """Проверяем, справляется ли API с очень длинными данными"""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    large_text = "A" * 10_000  # 10 тысяч символов

    data = {"company_name": large_text, "description": large_text}
    response = test_app.post(
        f"/api/companies/add?company={seed_company['company_id']}", headers=headers, json=data)

    assert response.status_code == 422, "Ожидали ошибку валидации из-за длинного текста!"
