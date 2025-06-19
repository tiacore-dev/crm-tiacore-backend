from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.database.models import BankAccount, Bills, Contract


@pytest.mark.asyncio
async def test_add_bill(
    test_app: AsyncClient,
    jwt_token_admin,
    seed_bank_account: BankAccount,
    seed_contract: Contract,
):
    """Тест добавления нового счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "bank_account": str(seed_bank_account.id),
        "bill_number": "INV-2024-001",
        "bill_date": 1710000000,
        "contract": str(seed_contract.id),
        "company": str(uuid4()),
    }

    response = await test_app.post("/api/bills/add", headers=headers, json=data)
    assert response.status_code == 201, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    data = response.json()
    bill = await Bills.filter(number="INV-2024-001").first()
    if bill:
        assert data["bill_id"] == str(bill.id)


@pytest.mark.asyncio
async def test_edit_bill(test_app: AsyncClient, jwt_token_admin, seed_bill: Bills):
    """Тест редактирования счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {"bill_number": "INV-2024-002"}

    response = await test_app.patch(
        f"/api/bills/{seed_bill.id}", headers=headers, json=data
    )

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    updated_bill = await Bills.filter(id=seed_bill.id).first()
    if updated_bill:
        assert updated_bill.number == "INV-2024-002"


@pytest.mark.asyncio
async def test_view_bill(test_app: AsyncClient, jwt_token_admin, seed_bill: Bills):
    """Тест просмотра информации о счете."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get(f"/api/bills/{seed_bill.id}", headers=headers)

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    response_data = response.json()
    assert response_data["bill_id"] == str(seed_bill.id)
    assert response_data["bill_number"] == seed_bill.number
    assert response_data["bill_date"] == seed_bill.date
    if seed_bill.contract:
        assert response_data["contract"] == str(seed_bill.contract.id)
    assert response_data["bank_account"] == str(seed_bill.bank_account.id)


@pytest.mark.asyncio
async def test_delete_bill(test_app: AsyncClient, jwt_token_admin, seed_bill: Bills):
    """Тест удаления счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.delete(f"/api/bills/{seed_bill.id}", headers=headers)
    assert response.status_code == 204, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    deleted_bill = await Bills.filter(id=seed_bill.id).first()
    assert deleted_bill is None


@pytest.mark.asyncio
async def test_get_all_bills(test_app: AsyncClient, jwt_token_admin, seed_bill: Bills):
    """Тест получения списка счетов."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get("/api/bills/all", headers=headers)
    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    response_data = response.json()
    assert response_data.get("total") >= 1
    bills = response_data.get("bills")
    assert any(bill["bill_id"] == str(seed_bill.id) for bill in bills)
