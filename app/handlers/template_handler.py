from io import BytesIO
from jinja2 import Environment
from docxtpl import DocxTemplate
from app.database.models import Acts, Bills
from app.utils.context_builders import build_act_context, build_bill_context, format_date


async def handle_bills(bill_id: str, template_bytes: bytes):
    bill = await Bills.get(bill_id=bill_id).prefetch_related(
        "bank_account__legal_entity__entity_type",
        "contract__buyer",
        "contract__seller",
        "contract__status",
        "details_in_bill__service"
    )

    context = await build_bill_context(bill)

    docx_bytes = generate_docx_from_bytes(template_bytes, context)

    return docx_bytes, bill.bill_number


async def handle_acts(act_id: str, template_bytes: bytes):
    act = await Acts.get_or_none(act_id=act_id).prefetch_related(
        "contract__buyer",
        "contract__seller",
        "details_in_act__service"
    )

    context = await build_act_context(act)
    docx_bytes = generate_docx_from_bytes(template_bytes, context)
    return docx_bytes, act.act_number


def generate_docx_from_bytes(template_bytes: bytes, context: dict) -> bytes:
    doc_stream = BytesIO(template_bytes)
    doc = DocxTemplate(doc_stream)

    # Настроим Jinja-среду
    jinja_env = Environment()
    jinja_env.filters["format_date"] = format_date  # 👈 добавляем фильтр

    # Рендер с кастомной Jinja2-средой
    doc.render(context, jinja_env=jinja_env)

    output_stream = BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    return output_stream.read()
