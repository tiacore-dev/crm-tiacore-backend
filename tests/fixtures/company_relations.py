import pytest
from app.database.models import Company, User, UserRole, UserCompanyRelation, EntityCompanyRelation, LegalEntity


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
async def seed_relation(seed_user, seed_company, seed_role_admin):
    user = await User.get_or_none(user_id=seed_user['user_id'])
    company = await Company.get_or_none(company_id=seed_company['company_id'])
    role = await UserRole.get_or_none(role_id=seed_role_admin['role_id'])
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


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_entity_relation(seed_legal_entity, seed_company, seed_role_admin):
    entity = await LegalEntity.get_or_none(legal_entity_id=seed_legal_entity['legal_entity_id'])
    company = await Company.get_or_none(company_id=seed_company['company_id'])

    relation = await EntityCompanyRelation.create(
        company=company,
        legal_entity=entity,
        relation_type="buyer"
    )
    return {
        "entity_company_relation_id": str(relation.entity_company_relation_id),
        "legal_entity": relation.legal_entity,
        "company": relation.company,
        "relation_type": relation.relation_type
    }
