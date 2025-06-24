from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tiacore_lib.utils.validate_helpers import validate_exists
from tortoise.expressions import Q
from tortoise.functions import Sum

from app.database.models import ActDetails, Acts, Contract
from app.dependencies.permissions import with_permission_and_seller_act_check
from app.pydantic_models.act_models import (
    ActCreateSchema,
    ActEditSchema,
    ActListResponseSchema,
    ActResponseSchema,
    ActSchema,
    act_filter_params,
)
from app.utils.permissions_get import ensure_seller_belongs_to_company

act_router = APIRouter()


@act_router.post(
    "/add",
    response_model=ActResponseSchema,
    summary="Добавить акт",
    status_code=status.HTTP_201_CREATED,
)
async def add_act(
    data: ActCreateSchema, context=Depends(require_permission_in_context("add_act"))
):
    contract = None
    if data.contract_id:
        contract = await Contract.get_or_none(id=data.contract_id)

        if not contract:
            raise HTTPException(status_code=400, detail="Контракт не найден")

        data.buyer_id = contract.buyer_id
        data.seller_id = contract.seller_id

    if not context.get("is_superadmin"):
        await ensure_seller_belongs_to_company(data.seller_id, context["company_id"])

    act = await Acts.create(**data.model_dump())
    return ActResponseSchema(act_id=act.id)


@act_router.patch("/{act_id}", response_model=ActResponseSchema, summary="Изменить акт")
async def update_act(
    act_id: UUID,
    data: ActEditSchema,
    _=with_permission_and_seller_act_check("edit_act"),
):
    act = await Acts.filter(id=act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    update_data = data.model_dump(exclude_unset=True)

    if "contract" in update_data:
        await validate_exists(Contract, data.contract_id, "Контракт")

    await act.update_from_dict(update_data)
    await act.save()

    return ActResponseSchema(act_id=act.id)


@act_router.delete(
    "/{act_id}", summary="Удалить акт", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_act(
    act_id: UUID, _=with_permission_and_seller_act_check("delete_act")
):
    act = await Acts.filter(id=act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    await act.delete()


@act_router.get(
    "/all", response_model=ActListResponseSchema, summary="Получение списка актов"
)
async def get_acts(
    filters: dict = Depends(act_filter_params),
    context=Depends(require_permission_in_context("get_all_acts")),
):
    try:
        query = Q()
        if context["is_superadmin"]:
            company_filter = filters.get("company")
            if company_filter:
                query &= Q(company_id=company_filter)
        else:
            query &= Q(company_id=context["company_id"])

        if filters.get("contract"):
            query &= Q(contract_id=filters["contract"])

        if filters.get("buyer"):
            query &= Q(buyer_id=filters["buyer"])

        if filters.get("seller"):
            query &= Q(seller_id=filters["seller"])

        if filters.get("act_date_from"):
            try:
                date_from = int(filters["act_date_from"])
                query &= Q(date__gte=date_from)
            except ValueError as e:
                raise HTTPException(
                    status_code=422,
                    detail="act_date_from должен быть целым числом (timestamp)",
                ) from e

        if filters.get("act_date_to"):
            try:
                date_to = int(filters["act_date_to"])
                query &= Q(date__lte=date_to)
            except ValueError as e:
                raise HTTPException(
                    status_code=422,
                    detail="act_date_to должен быть целым числом (timestamp)",
                ) from e

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        sort_field_map = {
            "act_number": "number",
            "act_date": "date",
            "status": "status",  # пример других возможных полей
        }

        sort_by = filters.get("sort_by", "act_number")
        sort_field = sort_field_map.get(sort_by)

        if not sort_field:
            raise HTTPException(
                status_code=422, detail=f"Некорректное поле сортировки: {sort_by}"
            )

        order = filters.get("order", "asc").lower()
        if order not in ("asc", "desc"):
            raise HTTPException(
                status_code=422, detail="order должен быть 'asc' или 'desc'"
            )

        # итоговое поле сортировки с направлением
        sort_expr = sort_field if order == "asc" else f"-{sort_field}"

        total_count = await Acts.filter(query).count()

        acts = (
            await Acts.filter(query)
            .order_by(sort_expr)
            .prefetch_related("contract")
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        act_sums = (
            await ActDetails.filter(id__in=[act.id for act in acts])
            .group_by("id")
            .annotate(total_summ=Sum("summ"))
            .values("id", "total_summ")
        )

        summ_map = {item["id"]: item["total_summ"] for item in act_sums}

        return ActListResponseSchema(
            total=total_count,
            acts=[
                ActSchema(
                    act_id=act.id,
                    contract=act.contract.id if act.contract else None,
                    act_number=act.number,
                    act_date=act.date,
                    buyer=act.buyer_id,
                    seller=act.seller_id,
                    company=act.company_id,
                    summ=summ_map.get(act.id, Decimal("0.00")),
                )
                for act in acts
            ],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@act_router.get("/{act_id}", response_model=ActSchema, summary="Просмотр одного акта")
async def get_act(act_id: UUID, _=with_permission_and_seller_act_check("view_act")):
    act = await Acts.filter(id=act_id).prefetch_related("contract").first()

    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    act_summ_records = (
        await ActDetails.filter(id=act_id)
        .group_by("id")
        .annotate(total_summ=Sum("summ"))
        .values("id", "total_summ")
    )

    act_summ = (
        Decimal(act_summ_records[0]["total_summ"] or "0.00")
        if act_summ_records
        else Decimal("0.00")
    )

    return ActSchema(
        act_id=act.id,
        contract=act.contract.id if act.contract else None,
        act_number=act.number,
        act_date=act.date,
        buyer=act.buyer_id,
        seller=act.seller_id,
        company=act.company_id,
        summ=Decimal(act_summ),
    )
