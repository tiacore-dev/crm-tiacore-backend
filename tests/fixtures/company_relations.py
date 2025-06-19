from uuid import uuid4

import pytest

from app.database.models import (
    EntityCompanyRelation,
)


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_entity_relation():
    relation = await EntityCompanyRelation.create(
        company=uuid4(), legal_entity=uuid4(), relation_type="buyer"
    )
    return relation
