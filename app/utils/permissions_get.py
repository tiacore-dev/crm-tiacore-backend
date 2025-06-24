from uuid import UUID

from fastapi import HTTPException
from loguru import logger

from app.database.models import (
    EntityCompanyRelation,
)


async def ensure_seller_belongs_to_company(seller, company_id: UUID):
    is_seller = await EntityCompanyRelation.exists(
        legal_entity_id=seller, company_id=company_id, relation_type="seller"
    )
    if not is_seller:
        logger.warning("Попытка использовать чужого продавца")
        raise HTTPException(
            status_code=403,
            detail="""Вы не можете действовать от имени юрлица, 
            не связанного с вашей компанией как продавец""",
        )
