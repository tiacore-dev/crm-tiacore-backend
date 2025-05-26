from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from tortoise.expressions import Q

from app.database.models import (
    Company,
    EntityCompanyRelation,
    LegalEntity,
    LegalEntityType,
    UserCompanyRelation,
)
from app.dependencies.permissions import with_permission_and_entity_company_check
from app.handlers.auth import get_current_user
from app.handlers.depends import require_permission_in_context
from app.pydantic_models.legal_entity_models import (
    LegalEntityCreateSchema,
    LegalEntityEditSchema,
    LegalEntityListResponseSchema,
    LegalEntityResponseSchema,
    LegalEntitySchema,
    LegalEntityShortSchema,
    inn_kpp_filter_params,
    legal_entity_filter_params,
)

entity_router = APIRouter()


@entity_router.post(
    "/add",
    response_model=LegalEntityResponseSchema,
    summary="Добавить юридическое лицо",
    status_code=status.HTTP_201_CREATED,
)
async def add_legal_entity(
    data: LegalEntityCreateSchema,
    context=Depends(require_permission_in_context("add_legal_entity")),
):
    try:
        entity_type = None
        # Проверяем, что пользователь действительно связан с этой компанией
        if not context.get("is_superadmin"):
            is_related = await UserCompanyRelation.exists(
                user_id=context["user"], company_id=data.company
            )
            if not is_related:
                raise HTTPException(
                    status_code=403, detail="Вы не имеете доступа к этой компании"
                )
        if data.entity_type is not None:
            entity_type = await LegalEntityType.get_or_none(
                legal_entity_type_id=data.entity_type
            )
            if not entity_type:
                raise HTTPException(status_code=400, detail="Тип юр. лица не найден")

        company = await Company.get_or_none(company_id=data.company)

        if not company:
            raise HTTPException(status_code=400, detail="Компания не найдена")

        if data.kpp:
            existing_entity = await LegalEntity.get_or_none(inn=data.inn, kpp=data.kpp)
        else:
            existing_entity = await LegalEntity.get_or_none(inn=data.inn)

        if existing_entity:
            logger.warning(f"Юрлицо с ИНН {data.inn} уже существует")
            raise HTTPException(
                status_code=400, detail=f"Юрлицо с ИНН {data.inn} уже существует"
            )

        entity = await LegalEntity.create(
            legal_entity_name=data.legal_entity_name,
            inn=data.inn,
            kpp=data.kpp,
            vat_rate=data.vat_rate,
            address=data.address,
            entity_type=entity_type,
            signer=data.signer,
        )

        await EntityCompanyRelation.create(
            company=company,
            legal_entity=entity,
            relation_type=data.relation_type,
            description=data.description,
        )
        return {"legal_entity_id": str(entity.legal_entity_id)}

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@entity_router.patch(
    "/{legal_entity_id}",
    response_model=LegalEntityResponseSchema,
    summary="Изменить юридическое лицо",
)
async def update_legal_entity(
    legal_entity_id: UUID,
    data: LegalEntityEditSchema,
    _=with_permission_and_entity_company_check("edit_legal_entity"),
):
    entity = await LegalEntity.filter(legal_entity_id=legal_entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Юридическое лицо не найдено")

    update_data = data.model_dump(exclude_unset=True)

    entity_type_id = update_data.pop("entity_type", None)
    if entity_type_id is not None:
        entity_type = await LegalEntityType.get_or_none(
            legal_entity_type_id=entity_type_id
        )
        if not entity_type:
            raise HTTPException(
                status_code=400, detail="Тип юридического лица не найден"
            )
        update_data["entity_type"] = entity_type

    await entity.update_from_dict(update_data)
    await entity.save()

    return {"legal_entity_id": str(entity.legal_entity_id)}


@entity_router.delete(
    "/{legal_entity_id}",
    summary="Удалить юридическое лицо",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_legal_entity(
    legal_entity_id: UUID,
    _=with_permission_and_entity_company_check("delete_legal_entity"),
):
    entity = await LegalEntity.filter(legal_entity_id=legal_entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Юридическое лицо не найдено")

    await entity.delete()
    return


@entity_router.get(
    "/all",
    response_model=LegalEntityListResponseSchema,
    summary="Получение списка юридических лиц",
)
async def get_legal_entities(
    filters: dict = Depends(legal_entity_filter_params),
    context: dict = Depends(require_permission_in_context("get_all_legal_entities")),
):
    try:
        query = Q()

        if context["is_superadmin"]:
            company_filter = filters.get("company")
            if company_filter:
                # супер-админ может фильтровать по компании
                query &= Q(entity_company_relations__company_id=company_filter)
            # иначе — без ограничений
        else:
            # Ищем все legal_entity_id, связанные с этими компаниями
            related_entity_ids = await EntityCompanyRelation.filter(
                company_id=context["company"]
            ).values_list("legal_entity_id", flat=True)

            if not related_entity_ids:
                return LegalEntityListResponseSchema(total=0, entities=[])

            query &= Q(legal_entity_id__in=related_entity_ids)

        if filters.get("entity_type"):
            query &= Q(entity_type_id=filters["entity_type"])

        total_count = await LegalEntity.filter(query).count()

        entities = (
            await LegalEntity.filter(query)
            .prefetch_related("entity_type", "entity_company_relations")
            .offset((filters["page"] - 1) * filters["page_size"])
            .limit(filters["page_size"])
        )

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
                    entity_type=entity.entity_type.legal_entity_type_id
                    if entity.entity_type
                    else None,
                    signer=entity.signer,
                )
                for entity in entities
            ],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@entity_router.get(
    "/get-buyers",
    response_model=LegalEntityListResponseSchema,
    summary="Получение списка buyers",
)
async def get_buyers(
    context: dict = Depends(require_permission_in_context("get_buyers")),
):
    try:
        # Ищем все legal_entity_id, связанные с этими компаниями
        related_entity_ids = await EntityCompanyRelation.filter(
            company_id=context["company"], relation_type="buyer"
        ).values_list("legal_entity_id", flat=True)

        if not related_entity_ids:
            return LegalEntityListResponseSchema(total=0, entities=[])

        total_count = await LegalEntity.filter(
            legal_entity_id__in=related_entity_ids
        ).count()
        entities = (
            await LegalEntity.filter(legal_entity_id__in=related_entity_ids)
            .prefetch_related("entity_type", "entity_company_relations")
            .all()
        )

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
                    entity_type=entity.entity_type.legal_entity_type_id
                    if entity.entity_type
                    else None,
                    signer=entity.signer,
                )
                for entity in entities
            ],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@entity_router.get(
    "/get-sellers",
    response_model=LegalEntityListResponseSchema,
    summary="Получение списка sellers",
)
async def get_sellers(
    context: dict = Depends(require_permission_in_context("get_sellers")),
):
    try:
        # Ищем все legal_entity_id, связанные с этими компаниями
        related_entity_ids = await EntityCompanyRelation.filter(
            company_id=context["company"], relation_type="seller"
        ).values_list("legal_entity_id", flat=True)

        if not related_entity_ids:
            return LegalEntityListResponseSchema(total=0, entities=[])

        total_count = await LegalEntity.filter(
            legal_entity_id__in=related_entity_ids
        ).count()
        entities = (
            await LegalEntity.filter(legal_entity_id__in=related_entity_ids)
            .prefetch_related("entity_type", "entity_company_relations")
            .all()
        )

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
                    entity_type=entity.entity_type.legal_entity_type_id
                    if entity.entity_type
                    else None,
                    signer=entity.signer,
                )
                for entity in entities
            ],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@entity_router.get(
    "/get-by-company",
    response_model=LegalEntityListResponseSchema,
    summary="Получение списка организаций по компании",
)
async def get_by_company(
    company_id: UUID = Query(..., description="ID компании"),
    _: dict = Depends(require_permission_in_context("get_by_company")),
):
    try:
        related_entity_ids = await EntityCompanyRelation.filter(
            company_id=company_id
        ).values_list("legal_entity_id", flat=True)

        if not related_entity_ids:
            return LegalEntityListResponseSchema(total=0, entities=[])

        total_count = await LegalEntity.filter(
            legal_entity_id__in=related_entity_ids
        ).count()
        entities = (
            await LegalEntity.filter(legal_entity_id__in=related_entity_ids)
            .prefetch_related("entity_type", "entity_company_relations")
            .all()
        )

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
                    entity_type=entity.entity_type.legal_entity_type_id
                    if entity.entity_type
                    else None,
                    signer=entity.signer,
                )
                for entity in entities
            ],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@entity_router.get(
    "/inn-kpp",
    response_model=LegalEntityShortSchema,
    summary="Получение организации по инн и кпп",
)
async def get_legal_entity_by_inn_kpp(
    filters: dict[str, Optional[str]] = Depends(inn_kpp_filter_params),
    _: dict = Depends(get_current_user),
):
    try:
        kpp = filters.get("kpp")
        if not kpp:
            entity = await LegalEntity.filter(inn=filters["inn"]).first()
        else:
            entity = await LegalEntity.filter(inn=filters["inn"], kpp=kpp).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Организация не найдена")
        return LegalEntityShortSchema(
            legal_entity_id=entity.legal_entity_id,
            legal_entity_name=entity.legal_entity_name,
        )
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@entity_router.get(
    "/{legal_entity_id}",
    response_model=LegalEntitySchema,
    summary="Просмотр одного юридического лица",
)
async def get_legal_entity(
    legal_entity_id: UUID,
    context: dict = Depends(require_permission_in_context("view_legal_entity")),
):
    entity = (
        await LegalEntity.filter(legal_entity_id=legal_entity_id)
        .prefetch_related("entity_company_relations__company", "entity_type")
        .first()
    )

    if not entity:
        raise HTTPException(status_code=404, detail="Юридическое лицо не найдено")

    # Получаем все связанные company_id
    related_company_ids = [
        rel.company.company_id for rel in entity.entity_company_relations
    ]

    if not context["is_superadmin"] and context["company"] not in related_company_ids:
        raise HTTPException(status_code=403, detail="Нет доступа к этой записи")

    return LegalEntitySchema(
        legal_entity_id=entity.legal_entity_id,
        legal_entity_name=entity.legal_entity_name,
        inn=entity.inn,
        kpp=entity.kpp,
        vat_rate=entity.vat_rate,
        address=entity.address,
        entity_type=entity.entity_type.legal_entity_type_id
        if entity.entity_type
        else None,
        signer=entity.signer,
    )
