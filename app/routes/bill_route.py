from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tiacore_lib.utils.validate_helpers import validate_exists
from tortoise.expressions import Q
from tortoise.functions import Sum

from app.database.models import (
    BillDetails,
    Bills,
    Contract,
)
from app.dependencies.permissions import with_permission_and_seller_bill_check
from app.pydantic_models.bill_models import (
    BillCreateSchema,
    BillEditSchema,
    BillListResponseSchema,
    BillResponseSchema,
    BillSchema,
    bill_filter_params,
)
from app.utils.permissions_get import ensure_seller_belongs_to_company

bill_router = APIRouter()


@bill_router.post(
    "/add",
    response_model=BillResponseSchema,
    summary="Добавить счет",
    status_code=status.HTTP_201_CREATED,
)
async def add_bill(
    data: BillCreateSchema,
    context=Depends(require_permission_in_context("add_bill")),
):
    contract = None
    if data.contract_id:
        contract = await Contract.get_or_none(id=data.contract_id)
        if not contract:
            raise HTTPException(status_code=400, detail="Контрсчет не найден")

        data.buyer_id = contract.buyer_id
        data.seller_id = contract.seller_id

    if not context.get("is_superadmin"):
        await ensure_seller_belongs_to_company(data.seller_id, context["company_id"])

    bill = await Bills.create(**data.model_dump())
    return BillResponseSchema(bill_id=bill.id)


@bill_router.patch(
    "/{bill_id}", response_model=BillResponseSchema, summary="Изменить счет"
)
async def update_bill(
    bill_id: UUID,
    data: BillEditSchema,
    _=with_permission_and_seller_bill_check("edit_bill"),
):
    bill = await Bills.filter(id=bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Счет не найден")

    update_data = data.model_dump(exclude_unset=True)

    if "contract" in update_data:
        await validate_exists(Contract, data.contract_id, "Контрсчет")

    await bill.update_from_dict(update_data)
    await bill.save()

    return BillResponseSchema(bill_id=bill.id)


@bill_router.delete(
    "/{bill_id}", summary="Удалить счет", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_bill(
    bill_id: UUID,
    check_bill_access=with_permission_and_seller_bill_check("delete_bill"),
):
    bill = await Bills.filter(id=bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Счет не найден")

    await bill.delete()


@bill_router.get(
    "/all", response_model=BillListResponseSchema, summary="Получение списка счетов"
)
async def get_bills(
    filters: dict = Depends(bill_filter_params),
    context=Depends(require_permission_in_context("get_all_bills")),
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

        if filters.get("bill_date_from"):
            try:
                date_from = int(filters["bill_date_from"])
                query &= Q(date__gte=date_from)
            except ValueError as e:
                raise HTTPException(
                    status_code=422,
                    detail="bill_date_from должен быть целым числом (timestamp)",
                ) from e

        if filters.get("bill_date_to"):
            try:
                date_to = int(filters["bill_date_to"])
                query &= Q(date__lte=date_to)
            except ValueError as e:
                raise HTTPException(
                    status_code=422,
                    detail="bill_date_to должен быть целым числом (timestamp)",
                ) from e

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        sort_by = filters.get("sort_by", "number")
        order = filters.get("order", "asc").lower()
        if order not in ("asc", "desc"):
            raise HTTPException(
                status_code=422, detail="order должен быть 'asc' или 'desc'"
            )

        sort_field = sort_by if order == "asc" else f"-{sort_by}"

        total_count = await Bills.filter(query).count()

        bills = (
            await Bills.filter(query)
            .order_by(sort_field)
            .prefetch_related("contract", "bank_account")
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        bill_sums = (
            await BillDetails.filter(id__in=[bill.id for bill in bills])
            .group_by("id")
            .annotate(total_summ=Sum("summ"))
            .values("id", "total_summ")
        )

        summ_map = {item["id"]: item["total_summ"] for item in bill_sums}

        return BillListResponseSchema(
            total=total_count,
            bills=[
                BillSchema(
                    bill_id=bill.id,
                    contract=bill.contract.id if bill.contract else None,
                    bank_account=bill.bank_account.id,
                    bill_number=bill.number,
                    bill_date=bill.date,
                    buyer=bill.buyer_id,
                    seller=bill.seller_id,
                    company=bill.company_id,
                    summ=summ_map.get(bill.id, Decimal("0.00")),
                )
                for bill in bills
            ],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@bill_router.get(
    "/{bill_id}", response_model=BillSchema, summary="Просмотр одного счета"
)
async def get_bill(bill_id: UUID, _=with_permission_and_seller_bill_check("view_bill")):
    bill = (
        await Bills.filter(id=bill_id)
        .prefetch_related("contract", "bank_account")
        .first()
    )

    if not bill:
        raise HTTPException(status_code=404, detail="Счет не найден")

    bill_summ_records = (
        await BillDetails.filter(id=bill_id)
        .group_by("id")
        .annotate(total_summ=Sum("summ"))
        .values("id", "total_summ")
    )

    bill_summ = (
        Decimal(bill_summ_records[0]["total_summ"] or "0.00")
        if bill_summ_records
        else Decimal("0.00")
    )

    return BillSchema(
        bill_id=bill.id,
        contract=bill.contract.id if bill.contract else None,
        bank_account=bill.bank_account.id,
        bill_number=bill.number,
        bill_date=bill.date,
        buyer=bill.buyer_id,
        seller=bill.seller_id,
        company=bill.company_id,
        summ=Decimal(bill_summ),
    )
