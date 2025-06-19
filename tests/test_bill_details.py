import pytest
from httpx import AsyncClient

from app.database.models import BillDetails, Bills, Service


@pytest.mark.asyncio
async def test_add_bill_detail(
    test_app: AsyncClient, jwt_token_admin, seed_bill: Bills, seed_service: Service
):
    """Тест добавления детали счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "bill": str(seed_bill.id),
        "service": str(seed_service.id),
        "quantity": 2.5,
        # "summ": 1500.75,
        "price": 20.0,
    }

    response = await test_app.post("/api/bill-details/add", headers=headers, json=data)
    assert response.status_code == 201, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    data = response.json()

    # Загружаем связанные объекты через prefetch_related
    bill_detail = (
        await BillDetails.filter(id=data["bill_detail_id"])
        .prefetch_related("bill", "service")
        .first()
    )
    assert bill_detail is not None
    assert str(bill_detail.bill.id) == str(seed_bill.id)
    assert str(bill_detail.service.id) == str(seed_service.id)
    assert bill_detail.quantity == 2.5
    assert bill_detail.summ == 2.5 * 20.0


@pytest.mark.asyncio
async def test_edit_bill_detail(
    test_app: AsyncClient, jwt_token_admin, seed_bill_detail: BillDetails
):
    """Тест редактирования детали счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "quantity": 5.0,
    }

    response = await test_app.patch(
        f"/api/bill-details/{seed_bill_detail.id}",
        headers=headers,
        json=data,
    )

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    updated_detail = await BillDetails.filter(id=seed_bill_detail.id).first()
    if updated_detail:
        assert updated_detail.quantity == 5.0


@pytest.mark.asyncio
async def test_view_bill_detail(
    test_app: AsyncClient, jwt_token_admin, seed_bill_detail: BillDetails
):
    """Тест просмотра информации о детали счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get(
        f"/api/bill-details/{seed_bill_detail.id}", headers=headers
    )

    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    response_data = response.json()

    assert str(response_data["bill_detail_id"]) == str(seed_bill_detail.id)
    assert str(response_data["bill"]) == str(seed_bill_detail.bill.id)
    assert str(response_data["service"]) == str(seed_bill_detail.service.id)
    assert float(response_data["quantity"]) == float(seed_bill_detail.quantity)


@pytest.mark.asyncio
async def test_delete_bill_detail(
    test_app: AsyncClient, jwt_token_admin, seed_bill_detail: BillDetails
):
    """Тест удаления детали счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.delete(
        f"/api/bill-details/{seed_bill_detail.id}", headers=headers
    )
    assert response.status_code == 204, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    deleted_detail = await BillDetails.filter(id=seed_bill_detail.id).first()
    assert deleted_detail is None


@pytest.mark.asyncio
async def test_get_all_bill_details(
    test_app: AsyncClient, jwt_token_admin, seed_bill_detail: BillDetails
):
    """Тест получения списка деталей счета."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get("/api/bill-details/all", headers=headers)
    assert response.status_code == 200, (
        f"Ошибка: {response.status_code}, {response.text}"
    )

    response_data = response.json()
    bill_details = response_data.get("bill_details")
    assert response_data.get("total") >= 1
    assert any(
        detail["bill_detail_id"] == str(seed_bill_detail.id) for detail in bill_details
    )
