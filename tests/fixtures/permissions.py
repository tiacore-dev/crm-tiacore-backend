import pytest
from app.database.models import (
    UserRole,
    Permissions,
    RolePermissionRelation,
    create_user,
    UserCompanyRelation,
    Company
)


@pytest.fixture
async def permission_edit_user():
    return await Permissions.create(permission_id="edit_user", permission_name="User Editor")


@pytest.fixture
async def role_with_edit_user(permission_edit_user):
    role = await UserRole.create(role_name="editor", role_system_name='admin')
    await RolePermissionRelation.create(role=role, permission=permission_edit_user)
    return role


@pytest.fixture
async def other_role():
    role = await UserRole.create(role_name="no_permission", role_system_name='user')
    return role


@pytest.fixture
async def seed_company_new():
    return await Company.create(company_name="TestCompany", description="...")


@pytest.fixture
async def other_company():
    return await Company.create(company_name="OtherCompany", description="...")


@pytest.fixture
async def seed_other_user(seed_company_new, other_role):
    user = await create_user(email='Test User', password='123', full_name="User", position='user')
    await UserCompanyRelation.create(user=user, company=seed_company_new, role=other_role)
    return user


@pytest.fixture
async def seed_other_user_wrong(other_company, other_role):
    user = await create_user(email='Test User', password='123', full_name="User", position='user')
    await UserCompanyRelation.create(user=user, company=other_company, role=other_role)
    return user

# 1. Без прав


@pytest.fixture
async def user_no_permission(seed_company_new, other_role):
    user = await create_user(email="noperm", full_name="No Perm", position="Dev", password='123')
    await UserCompanyRelation.create(user=user, company=seed_company_new, role=other_role)
    return user

# 2. С правами, но в другой компании


@pytest.fixture
async def user_wrong_company(role_with_edit_user, seed_company_new):
    user = await create_user(email="wrongco", full_name="Wrong Co", position="Dev", password="123")
    await UserCompanyRelation.create(user=user, company=seed_company_new, role=role_with_edit_user)
    return user

# 3. С правами и в нужной компании


@pytest.fixture
async def user_with_access(role_with_edit_user, seed_company_new):
    user = await create_user(email="withaccess", full_name="With Access", position="Dev", password="123")
    await UserCompanyRelation.create(user=user, company=seed_company_new, role=role_with_edit_user)
    return user
