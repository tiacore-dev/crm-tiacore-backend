import pytest
from app.database.models import Company, LegalEntity, LegalEntityType, EntityCompanyRelation


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_legal_entity(seed_company, seed_legal_entity_type):
    company = await Company.get_or_none(company_id=seed_company["company_id"])
    entity_type = await LegalEntityType.get_or_none(legal_entity_type_id=seed_legal_entity_type["legal_entity_type_id"])

    if not company or not entity_type:
        raise ValueError(
            "Ошибка: Не удалось получить объекты Company или LegalEntityType")

    legal_entity = await LegalEntity.create(
        legal_entity_name="Test Legal Entity",
        inn="123456789012",
        kpp="123456789",
        vat_rate=20,
        address="Test Address",
        entity_type=entity_type,
        signer="Test Signer",
    )

    # Создаем связь entity ↔ company
    await EntityCompanyRelation.create(
        company=company,
        legal_entity=legal_entity,
        relation_type="seller"  # или "buyer"
    )

    return {
        "legal_entity_id": str(legal_entity.legal_entity_id),
        "legal_entity_name": legal_entity.legal_entity_name,
        "inn": legal_entity.inn,
        "kpp": legal_entity.kpp,
        "vat_rate": legal_entity.vat_rate,
        "address": legal_entity.address,
        "signer": legal_entity.signer,
        "entity_type": str(entity_type.legal_entity_type_id),

    }


@pytest.mark.usefixtures("setup_db")
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_legal_entity_buyer(seed_company, seed_legal_entity_type):
    """Создает тестовое юридическое лицо, передавая объекты вместо ID."""

    # Получаем объекты из базы
    company = await Company.get_or_none(company_id=seed_company["company_id"])
    entity_type = await LegalEntityType.get_or_none(legal_entity_type_id=seed_legal_entity_type["legal_entity_type_id"])

    if not company or not entity_type:
        raise ValueError(
            "Ошибка: Не удалось получить объекты Company или LegalEntityType")

    # Создаем юридическое лицо, передавая объекты
    legal_entity = await LegalEntity.create(
        legal_entity_name="Test Legal Entity Buyer",
        inn="123456789013",
        kpp="123456789",
        vat_rate=20,
        address="Test Address",
        entity_type=entity_type,
        signer="Test Signer",
    )

    await EntityCompanyRelation.create(legal_entity=legal_entity, company=company, relation_type="buyer")

    return {
        "legal_entity_id": str(legal_entity.legal_entity_id),
        "legal_entity_name": legal_entity.legal_entity_name,
        "inn": legal_entity.inn,
        "kpp": legal_entity.kpp,
        "vat_rate": legal_entity.vat_rate,
        "address": legal_entity.address,
        "signer": legal_entity.signer,
        "entity_type": str(legal_entity.entity_type.legal_entity_type_id),
    }
