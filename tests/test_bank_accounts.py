import pytest
from httpx import AsyncClient
from app.database.models import BankAccount


@pytest.mark.asyncio
async def test_add_bank_account(test_app: AsyncClient, jwt_token_user, seed_legal_entity):
    """Тест добавления нового банковского счета."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    data = {
        "account_number": "12345678901234567890",
        "bank_name": "Test Bank",
        "bank_bic": "123456789",
        "bank_corr_account": "98765432109876543210",
        "legal_entity": seed_legal_entity["legal_entity_id"]
    }

    response = test_app.post("/api/bank-accounts/add",
                             headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    bank_account = await BankAccount.filter(account_number="12345678901234567890").first()
    assert bank_account is not None
    assert response_data["bank_account_id"] == str(
        bank_account.bank_account_id)


@pytest.mark.asyncio
async def test_edit_bank_account(test_app: AsyncClient, jwt_token_user, seed_bank_account):
    """Тест редактирования банковского счета."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}
    data = {
        "bank_name": "Updated Bank Name",
        "bank_bic": "987654321"
    }

    response = test_app.patch(
        f"/api/bank-accounts/{seed_bank_account['bank_account_id']}",
        headers=headers,
        json=data
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что данные обновились в БД
    updated_bank_account = await BankAccount.filter(bank_account_id=seed_bank_account["bank_account_id"]).first()
    assert updated_bank_account is not None
    assert updated_bank_account.bank_name == "Updated Bank Name"
    assert updated_bank_account.bank_bic == "987654321"


@pytest.mark.asyncio
async def test_view_bank_account(test_app: AsyncClient, jwt_token_user, seed_bank_account):
    """Тест просмотра информации о банковском счете."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get(
        f"/api/bank-accounts/{seed_bank_account['bank_account_id']}",
        headers=headers
    )

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert response_data["bank_account_id"] == str(
        seed_bank_account["bank_account_id"])
    assert response_data["account_number"] == seed_bank_account["account_number"]
    assert response_data["bank_name"] == seed_bank_account["bank_name"]
    assert response_data["bank_bic"] == seed_bank_account["bank_bic"]
    assert response_data["bank_corr_account"] == seed_bank_account["bank_corr_account"]


@pytest.mark.asyncio
async def test_delete_bank_account(test_app: AsyncClient, jwt_token_user, seed_bank_account):
    """Тест удаления банковского счета."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.delete(
        f"/api/bank-accounts/{seed_bank_account['bank_account_id']}",
        headers=headers
    )

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    # Проверяем, что банковский счет удален
    deleted_bank_account = await BankAccount.filter(bank_account_id=seed_bank_account["bank_account_id"]).first()
    assert deleted_bank_account is None


@pytest.mark.asyncio
async def test_get_bank_accounts(test_app: AsyncClient, jwt_token_user, seed_bank_account):
    """Тест получения списка банковских счетов с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_user['access_token']}"}

    response = test_app.get("/api/bank-accounts/all", headers=headers)

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    bank_accounts = response_data.get('bank_accounts')
    assert response_data.get('total') >= 1
    assert isinstance(bank_accounts, list)
    assert any(account["bank_account_id"] == seed_bank_account["bank_account_id"]
               for account in bank_accounts)
