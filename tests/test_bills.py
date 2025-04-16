import pytest
from httpx import AsyncClient
from app.database.models import Bills


@pytest.mark.asyncio
async def test_add_bill(test_app: AsyncClient, jwt_token_admin, seed_bank_account, seed_contract):
    """Тест добавления нового счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "bank_account": seed_bank_account["bank_account_id"],
        "bill_number": "INV-2024-001",
        "bill_date": 1710000000,
        "contract": seed_contract["contract_id"]
    }

    response = test_app.post("/api/bills/add", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    data = response.json()
    bill = await Bills.filter(bill_number="INV-2024-001").first()
    assert data["bill_id"] == str(bill.bill_id)


@pytest.mark.asyncio
async def test_edit_bill(test_app: AsyncClient, jwt_token_admin, seed_bill):
    """Тест редактирования счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "bill_number": "INV-2024-002"
    }

    response = test_app.patch(
        f"/api/bills/{seed_bill['bill_id']}",
        headers=headers,
        json=data
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    updated_bill = await Bills.filter(bill_id=seed_bill["bill_id"]).first()
    assert updated_bill.bill_number == "INV-2024-002"


@pytest.mark.asyncio
async def test_view_bill(test_app: AsyncClient, jwt_token_admin, seed_bill):
    """Тест просмотра информации о счете."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.get(
        f"/api/bills/{seed_bill['bill_id']}",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert response_data["bill_id"] == str(seed_bill["bill_id"])
    assert response_data["bill_number"] == seed_bill["bill_number"]
    assert response_data["bill_date"] == seed_bill["bill_date"]
    assert response_data["contract"] == seed_bill["contract"]
    assert response_data["bank_account"] == seed_bill["bank_account"]


@pytest.mark.asyncio
async def test_delete_bill(test_app: AsyncClient, jwt_token_admin, seed_bill):
    """Тест удаления счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.delete(
        f"/api/bills/{seed_bill['bill_id']}", headers=headers)
    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    deleted_bill = await Bills.filter(bill_id=seed_bill["bill_id"]).first()
    assert deleted_bill is None


@pytest.mark.asyncio
async def test_get_all_bills(test_app: AsyncClient, jwt_token_admin, seed_bill):
    """Тест получения списка счетов."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = test_app.get("/api/bills/all", headers=headers)
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert response_data.get('total') >= 1
    bills = response_data.get('bills')
    assert any(bill["bill_id"] == seed_bill["bill_id"]
               for bill in bills)
