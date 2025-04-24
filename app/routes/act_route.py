from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import Acts, Contract, LegalEntity, EntityCompanyRelation
from app.pydantic_models.act_models import (
    ActCreateSchema,
    ActResponseSchema,
    ActEditSchema,
    act_filter_params,
    ActSchema,
    ActListResponseSchema
)
from app.handlers.depends import require_permission_in_context
from app.dependencies.permissions import with_permission_and_seller_company_check
from app.utils.permissions_get import ensure_seller_belongs_to_company


act_router = APIRouter()


@act_router.post(
    "/add",
    response_model=ActResponseSchema,
    summary="Добавить акт",
    status_code=status.HTTP_201_CREATED
)
async def add_act(
    data: ActCreateSchema,
    context=Depends(require_permission_in_context("add_act"))
):
    try:
        contract = None
        if data.contract:
            contract = await Contract.get_or_none(contract_id=data.contract).prefetch_related("buyer", "seller")

            if not contract:
                raise HTTPException(
                    status_code=400, detail="Контракт не найден")

            data.buyer = contract.buyer.legal_entity_id
            data.seller = contract.seller.legal_entity_id
        buyer = await LegalEntity.get_or_none(legal_entity_id=data.buyer)
        seller = await LegalEntity.get_or_none(legal_entity_id=data.seller)
        if not buyer or not seller:
            raise HTTPException(
                status_code=400, detail="Юр. лица не найдены")

        if not context.get("is_superadmin"):
            await ensure_seller_belongs_to_company(seller, context["company"])

        act = await Acts.create(
            act_number=data.act_number,
            act_date=data.act_date,
            contract=contract,
            buyer=buyer,
            seller=seller
        )
        return {"act_id": str(act.act_id)}

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@act_router.patch(
    "/{act_id}",
    response_model=ActResponseSchema,
    summary="Изменить акт"
)
async def update_act(act_id: UUID, data: ActEditSchema, check_act_access=with_permission_and_seller_company_check(
    permission="edit_act",
    model=Acts,
    model_name="act"
)):
    act = await Acts.filter(act_id=act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    update_data = data.dict(exclude_unset=True)

    if "contract" in update_data:
        contract = await Contract.get_or_none(contract_id=update_data["contract"])
        if not contract:
            raise HTTPException(status_code=400, detail="Контракт не найден")
        update_data["contract"] = contract

    if data.buyer:
        buyer = await LegalEntity.get_or_none(legal_entity_id=data.buyer)
        if not buyer:
            raise HTTPException(status_code=400, detail="Покупатель не найден")
        update_data["buyer"] = buyer

    if data.seller:
        seller = await LegalEntity.get_or_none(legal_entity_id=data.seller)
        if not seller:
            raise HTTPException(status_code=400, detail="Продавец не найден")
        update_data["seller"] = seller

    await act.update_from_dict(update_data)
    await act.save()

    return {"act_id": str(act.act_id)}


@act_router.delete(
    "/{act_id}",
    summary="Удалить акт",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_act(act_id: UUID, check_act_access=with_permission_and_seller_company_check(
    permission="delete_act",
    model=Acts,
    model_name="act"
)):
    act = await Acts.filter(act_id=act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    await act.delete()


@act_router.get(
    "/all",
    response_model=ActListResponseSchema,
    summary="Получение списка актов"
)
async def get_acts(filters: dict = Depends(act_filter_params), context=Depends(require_permission_in_context("get_all_acts"))):
    try:
        query = Q()
        if not context.get("is_superadmin"):
            seller_entity_ids = await EntityCompanyRelation.filter(
                company_id=context["company"],
                relation_type="seller"
            ).values_list("legal_entity_id", flat=True)
            query &= Q(seller_id__in=seller_entity_ids)

        if filters.get("contract"):
            query &= Q(contract_id=filters["contract"])

        if filters.get("act_date_from"):
            try:
                date_from = int(filters["act_date_from"])
                query &= Q(act_date__gte=date_from)
            except ValueError as e:
                raise HTTPException(
                    status_code=422, detail="act_date_from должен быть целым числом (timestamp)") from e

        if filters.get("act_date_to"):
            try:
                date_to = int(filters["act_date_to"])
                query &= Q(act_date__lte=date_to)
            except ValueError as e:
                raise HTTPException(
                    status_code=422, detail="act_date_to должен быть целым числом (timestamp)") from e

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        sort_by = filters.get("sort_by", "act_date")
        order = filters.get("order", "asc").lower()
        if order not in ("asc", "desc"):
            raise HTTPException(
                status_code=422, detail="order должен быть 'asc' или 'desc'")

        sort_field = sort_by if order == "asc" else f"-{sort_by}"

        total_count = await Acts.filter(query).count()

        acts = await Acts.filter(query).order_by(sort_field).prefetch_related("contract", "buyer", "seller").offset((page - 1) * page_size).limit(page_size)

        return ActListResponseSchema(
            total=total_count,
            acts=[
                ActSchema(
                    act_id=act.act_id,
                    contract=act.contract.contract_id if act.contract else None,
                    act_number=act.act_number,
                    act_date=act.act_date,
                    buyer=act.buyer.legal_entity_id,
                    seller=act.seller.legal_entity_id
                )
                for act in acts
            ]
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@act_router.get(
    "/{act_id}",
    response_model=ActSchema,
    summary="Просмотр одного акта"
)
async def get_act(act_id: UUID, check_act_access=with_permission_and_seller_company_check(
    permission="view_act",
    model=Acts,
    model_name="act"
)):
    act = await Acts.filter(act_id=act_id).prefetch_related("contract", "buyer", "seller").first()

    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    return ActSchema(
        act_id=act.act_id,
        contract=act.contract.contract_id if act.contract else None,
        act_number=act.act_number,
        act_date=act.act_date,
        buyer=act.buyer.legal_entity_id,
        seller=act.seller.legal_entity_id
    )
