from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from tortoise.contrib.pydantic import pydantic_model_creator
from loguru import logger
from app.database.models import LegalEntity, LegalEntityType, Company
from app.pydantic_models.legal_entity_models import (
    LegalEntityCreateSchema,
    LegalEntityResponseSchema,
    LegalEntityEditSchema,
    legal_entity_filter_params
)

LegalEntitySchema = pydantic_model_creator(
    LegalEntity, name="LegalEntitySchema")

entity_router = APIRouter()


@entity_router.post("/add", response_model=LegalEntityResponseSchema, summary="Добавить юридическое лицо", status_code=status.HTTP_201_CREATED)
async def add_legal_entity(data: LegalEntityCreateSchema):
    try:
        entity_type = await LegalEntityType.get_or_none(legal_entity_type_id=data.entity_type)
        company = await Company.get_or_none(company_id=data.company)

        if not entity_type or not company:
            raise HTTPException(
                status_code=400, detail="Компания или тип юр. лица не найдены")

        entity = await LegalEntity.create(
            legal_entity_name=data.legal_entity_name,
            inn=data.inn,
            kpp=data.kpp,
            vat_rate=data.vat_rate,
            address=data.address,
            entity_type=entity_type,
            signer=data.signer,
            company=company,
            description=data.description,
        )
        return {"legal_entity_id": str(entity.legal_entity_id)}

    except Exception as e:
        logger.exception("Ошибка при создании юридического лица")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@entity_router.patch("/{legal_entity_id}", response_model=LegalEntityResponseSchema, summary="Изменить юридическое лицо")
async def update_legal_entity(legal_entity_id: UUID, data: LegalEntityEditSchema):
    entity = await LegalEntity.filter(legal_entity_id=legal_entity_id).first()
    if not entity:
        raise HTTPException(
            status_code=404, detail="Юридическое лицо не найдено")

    update_data = data.dict(exclude_unset=True)

    if "entity_type" in update_data:
        entity_type = await LegalEntityType.get_or_none(legal_entity_type_id=update_data["entity_type"])
        if not entity_type:
            raise HTTPException(
                status_code=400, detail="Тип юридического лица не найден")
        update_data["entity_type"] = entity_type

    if "company" in update_data:
        company = await Company.get_or_none(company_id=update_data["company"])
        if not company:
            raise HTTPException(status_code=400, detail="Компания не найдена")
        update_data["company"] = company

    await entity.update_from_dict(update_data)
    await entity.save()

    return {"legal_entity_id": str(entity.legal_entity_id)}


@entity_router.delete("/{legal_entity_id}", summary="Удалить юридическое лицо", status_code=status.HTTP_204_NO_CONTENT)
async def delete_legal_entity(legal_entity_id: UUID):
    entity = await LegalEntity.filter(legal_entity_id=legal_entity_id).first()
    if not entity:
        raise HTTPException(
            status_code=404, detail="Юридическое лицо не найдено")

    await entity.delete()
    # return {"message": "Юридическое лицо удалено"}


@entity_router.get("/all", response_model=List[LegalEntitySchema], summary="Получение списка юридических лиц")
async def get_legal_entities(filters: dict = Depends(legal_entity_filter_params)):
    try:
        query = Q()
        if filters.get("company"):
            query &= Q(company_id=filters["company"])
        if filters.get("entity_type"):
            query &= Q(legal_entity_type_id=filters["entity_type"])

        entities = await LegalEntity.filter(query) \
            .prefetch_related("company", "entity_type") \
            .offset((filters["page"] - 1) * filters["page_size"]) \
            .limit(filters["page_size"])

        return [await LegalEntitySchema.from_tortoise_orm(entity) for entity in entities]

    except Exception as e:
        logger.exception("Ошибка при получении списка юридических лиц")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@entity_router.get("/{legal_entity_id}", response_model=LegalEntitySchema, summary="Просмотр одного юридического лица")
async def get_legal_entity(legal_entity_id: UUID):
    entity = await LegalEntity.filter(legal_entity_id=legal_entity_id) \
        .prefetch_related("company", "entity_type") \
        .first()

    if not entity:
        raise HTTPException(
            status_code=404, detail="Юридическое лицо не найдено")

    return await LegalEntitySchema.from_tortoise_orm(entity)
