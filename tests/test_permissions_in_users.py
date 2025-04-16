from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_edit_user_no_permission(
    test_app: AsyncClient,
    get_token_for_user,
    user_no_permission,
    seed_other_user,
    seed_company_new
):
    token = await get_token_for_user(user_no_permission)
    response = test_app.patch(
        f"/api/users/{seed_other_user.user_id}?company={seed_company_new.company_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Hacker"}
    )
    assert response.status_code == 403
    assert "Недостаточно прав" in response.text  # 💥 для юзера без разрешения


@pytest.mark.asyncio
async def test_edit_user_wrong_company(
    test_app: AsyncClient,
    get_token_for_user,
    user_wrong_company,
    seed_other_user_wrong,
    seed_company_new
):
    token = await get_token_for_user(user_wrong_company)
    response = test_app.patch(
        f"/api/users/{seed_other_user_wrong.user_id}?company={seed_company_new.company_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Wrong Place"}
    )
    assert response.status_code == 403
    assert "других компаний" in response.text  # 💥 для юзера не из этой компании


@pytest.mark.asyncio
async def test_edit_user_with_access(
    test_app: AsyncClient,
    get_token_for_user,
    user_with_access,
    seed_other_user,
    seed_company_new
):
    token = await get_token_for_user(user_with_access)

    response = test_app.patch(
        f"/api/users/{seed_other_user.user_id}?company={seed_company_new.company_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Correct User"}
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == str(seed_other_user.user_id)
