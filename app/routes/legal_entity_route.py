from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import LegalEntity, LegalEntityType, Company
from app.pydantic_models.legal_entity_models import (
    LegalEntityCreateSchema,
    LegalEntityResponseSchema,
    LegalEntityEditSchema,
    legal_entity_filter_params,
    LegalEntitySchema,
    LegalEntityListResponseSchema
)
from app.dependencies.permissions import with_permission_and_entity_company_check
from app.handlers.depends import require_permission_in_context


entity_router = APIRouter()


@entity_router.post("/add", response_model=LegalEntityResponseSchema, summary="Добавить юридическое лицо", status_code=status.HTTP_201_CREATED)
async def add_legal_entity(data: LegalEntityCreateSchema, context=Depends(require_permission_in_context("add_legal_entity"))):
    try:
        entity_type = await LegalEntityType.get_or_none(legal_entity_type_id=data.entity_type)
        company = await Company.get_or_none(company_id=data.company)

        if not entity_type or not company:
            raise HTTPException(
                status_code=400, detail="Компания или тип юр. лица не найдены")

        existing_entity = await LegalEntity.get_or_none(inn=data.inn)
        if existing_entity:
            logger.warning(
                f"Юрлицо с ИНН {data.inn} уже существует")
            raise HTTPException(
                status_code=400,
                detail=f"Юрлицо с ИНН {data.inn} уже существует"
            )

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

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при создании юридического лица")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@entity_router.patch("/{legal_entity_id}", response_model=LegalEntityResponseSchema, summary="Изменить юридическое лицо")
async def update_legal_entity(legal_entity_id: UUID, data: LegalEntityEditSchema, context=with_permission_and_entity_company_check("edit_legal_entity")):
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
async def delete_legal_entity(legal_entity_id: UUID,  context=with_permission_and_entity_company_check("delete_legal_entity")):
    entity = await LegalEntity.filter(legal_entity_id=legal_entity_id).first()
    if not entity:
        raise HTTPException(
            status_code=404, detail="Юридическое лицо не найдено")

    await entity.delete()
    # return {"message": "Юридическое лицо удалено"}


@entity_router.get(
    "/all",
    response_model=LegalEntityListResponseSchema,
    summary="Получение списка юридических лиц"
)
async def get_legal_entities(
    filters: dict = Depends(legal_entity_filter_params),
    context: dict = Depends(
        require_permission_in_context("get_all_entities"))
):
    try:
        query = Q()

        company_filter = filters.get("company")

        if context["is_superadmin"]:
            if company_filter:
                query &= Q(company_id=company_filter)
            # иначе — без ограничений
        else:
            # у обычного пользователя должен быть контекст компании
            query &= Q(company_id=context["company"])

        if filters.get("entity_type"):
            query &= Q(entity_type_id=filters["entity_type"])

        total_count = await LegalEntity.filter(query).count()

        entities = await LegalEntity.filter(query) \
            .prefetch_related("company", "entity_type") \
            .offset((filters["page"] - 1) * filters["page_size"]) \
            .limit(filters["page_size"])

        return LegalEntityListResponseSchema(
            total=total_count,
            entities=[
                LegalEntitySchema(
                    legal_entity_id=entity.legal_entity_id,
                    legal_entity_name=entity.legal_entity_name,
                    inn=entity.inn,
                    kpp=entity.kpp,
                    vat_rate=entity.vat_rate,
                    address=entity.address,
                    entity_type=entity.entity_type.legal_entity_type_id,
                    signer=entity.signer,
                    company=entity.company.company_id,
                    description=entity.description
                )
                for entity in entities
            ]
        )

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при получении списка юридических лиц")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@entity_router.get(
    "/{legal_entity_id}",
    response_model=LegalEntitySchema,
    summary="Просмотр одного юридического лица"
)
async def get_legal_entity(legal_entity_id: UUID, context: dict = Depends(require_permission_in_context("view_entity"))):
    entity = await LegalEntity.filter(legal_entity_id=legal_entity_id) \
        .prefetch_related("company", "entity_type") \
        .first()

    if not entity:
        raise HTTPException(
            status_code=404, detail="Юридическое лицо не найдено")

    if not context["is_superadmin"] and entity.company.company_id != context["company"]:
        raise HTTPException(
            status_code=403, detail="Нет доступа к этой записи")

    return LegalEntitySchema(
        legal_entity_id=entity.legal_entity_id,
        legal_entity_name=entity.legal_entity_name,
        inn=entity.inn,
        kpp=entity.kpp,
        vat_rate=entity.vat_rate,
        address=entity.address,
        entity_type=entity.entity_type.legal_entity_type_id,  # Теперь ID
        signer=entity.signer,
        company=entity.company.company_id,  # Теперь ID
        description=entity.description
    )
