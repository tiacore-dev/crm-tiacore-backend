import pytest
from app.database.models import Company, User, UserRole, UserCompanyRelation


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_company():
    """Добавляет тестового пользователя в базу перед тестом."""
    company = await Company.create(
        company_name="Test Company",
        description="Description"
    )
    return {
        "company_id": str(company.company_id),
        "company_name": company.company_name,
        "description": company.description

    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_relation(seed_user, seed_company, seed_role):
    user = await User.get_or_none(user_id=seed_user['user_id'])
    company = await Company.get_or_none(company_id=seed_company['company_id'])
    role = await UserRole.get_or_none(role_id=seed_role['role_id'])
    relation = await UserCompanyRelation.create(
        company=company,
        user=user,
        role=role
    )
    return {
        "user_company_id": str(relation.user_company_id),
        "user": relation.user,
        "company": relation.company,
        "role": relation.role
    }
