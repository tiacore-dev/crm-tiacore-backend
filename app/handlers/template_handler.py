from uuid import UUID

from fastapi import HTTPException

from app.database.models import Acts, Bills
from app.utils.context_builders import build_act_context, build_bill_context


async def handle_bills(bill_id: UUID):
    bill = await Bills.get_or_none(id=bill_id).prefetch_related(
        "bank_account__legal_entity__entity_type",
        "contract__buyer_id",
        "contract__seller_id",
        "contract__status",
        "details_in_bill__service",
    )

    if not bill:
        raise HTTPException(status_code=404, detail="Счёт не найден")

    context = await build_bill_context(bill)

    return context, bill.number


async def handle_acts(act_id: UUID):
    act = await Acts.get_or_none(id=act_id).prefetch_related(
        "contract__buyer_id",
        "contract__seller_id",
        "details_in_act__service",
    )

    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    context = await build_act_context(act)

    return context, act.number
