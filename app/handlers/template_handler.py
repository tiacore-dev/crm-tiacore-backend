from app.database.models import Acts, Bills
from app.utils.context_builders import build_act_context, build_bill_context


async def handle_bills(bill_id: str):
    bill = await Bills.get(bill_id=bill_id).prefetch_related(
        "bank_account__legal_entity__entity_type",
        "contract__buyer",
        "contract__seller",
        "contract__status",
        "details_in_bill__service"
    )

    context = await build_bill_context(bill)

    return context, bill.bill_number


async def handle_acts(act_id: str):
    act = await Acts.get_or_none(act_id=act_id).prefetch_related(
        "contract__buyer",
        "contract__seller",
        "details_in_act__service"
    )

    context = await build_act_context(act)

    return context, act.act_number
