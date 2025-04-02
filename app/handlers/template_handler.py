from io import BytesIO
from jinja2 import Environment
from docxtpl import DocxTemplate
from openpyxl import load_workbook
from app.database.models import Acts, Bills
from app.utils.context_builders import build_act_context, build_bill_context, format_date, flatten_context


async def handle_bills(bill_id: str, template_bytes: bytes, extention: str):
    bill = await Bills.get(bill_id=bill_id).prefetch_related(
        "bank_account__legal_entity__entity_type",
        "contract__buyer",
        "contract__seller",
        "contract__status",
        "details_in_bill__service"
    )

    context = await build_bill_context(bill)
    document_bytes = None

    if extention == "docx":
        document_bytes = generate_docx_from_bytes(template_bytes, context)
    elif extention == "xlsx":
        document_bytes = generate_excel_from_template(template_bytes, context)

    return document_bytes, bill.bill_number


async def handle_acts(act_id: str, template_bytes: bytes, extention: str):
    act = await Acts.get_or_none(act_id=act_id).prefetch_related(
        "contract__buyer",
        "contract__seller",
        "details_in_act__service"
    )

    context = await build_act_context(act)
    document_bytes = None

    if extention == "docx":
        document_bytes = generate_docx_from_bytes(template_bytes, context)
    elif extention == "xlsx":
        document_bytes = generate_excel_from_template(template_bytes, context)

    return document_bytes, act.act_number


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


def generate_excel_from_template(template_bytes: bytes, context: dict) -> bytes:
    flat_ctx = flatten_context(context)

    input_stream = BytesIO(template_bytes)
    workbook = load_workbook(input_stream)
    sheet = workbook.active

    for row in sheet.iter_rows():
        for cell in row:
            if isinstance(cell.value, str):
                for key, value in flat_ctx.items():
                    placeholder = f"{{{{ {key} }}}}"
                    if placeholder in cell.value:
                        cell.value = cell.value.replace(
                            placeholder, str(value))

    output_stream = BytesIO()
    workbook.save(output_stream)
    output_stream.seek(0)
    return output_stream.read()
