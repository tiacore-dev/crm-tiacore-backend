import datetime
from app.database.models import Bills, Acts


def format_date(timestamp: int) -> str:
    try:
        return datetime.datetime.fromtimestamp(int(timestamp)).strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return "–"


def flatten_context(obj, parent_key='', sep='.') -> dict:
    """
    Рекурсивно разворачивает вложенные dict и списки в плоский словарь:
    {
        "act.details.0.service.service_name": "Имя услуги",
        ...
    }
    """
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            items.update(flatten_context(v, new_key, sep=sep))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            items.update(flatten_context(v, new_key, sep=sep))
    else:
        items[parent_key] = obj
    return items


async def build_bill_context(bill: Bills) -> dict:

    def legal_entity_to_dict(entity):
        return {
            "legal_entity_name": entity.legal_entity_name,
            "inn": entity.inn,
            "kpp": entity.kpp,
            "vat_rate": entity.vat_rate,
            "address": entity.address,
            "signer": entity.signer,
            "entity_type": getattr(entity.entity_type, "status_name", None)
        }

    return {
        "bill": {
            "bill_id": str(bill.bill_id),
            "bill_number": bill.bill_number,
            "bill_date": format_date(bill.bill_date),
            "contract": {
                "contract_id": str(bill.contract.contract_id),
                "contract_name": bill.contract.contract_name,
                "contract_date": format_date(bill.contract.contract_date),
                "buyer": legal_entity_to_dict(bill.contract.buyer),
                "seller": legal_entity_to_dict(bill.contract.seller),
                "status": getattr(bill.contract.status, "status_name", None)
            },
            "bank_account": {
                "account_number": bill.bank_account.account_number,
                "bank_name": bill.bank_account.bank_name,
                "bank_bic": bill.bank_account.bank_bic,
                "bank_corr_account": bill.bank_account.bank_corr_account,
                "legal_entity": legal_entity_to_dict(bill.bank_account.legal_entity)
            },
            "details": [
                {
                    "service": {
                        "service_name": detail.service.service_name,
                        "service_id": str(detail.service.service_id),
                    },
                    "quantity": float(detail.quantity),
                    "summ": float(detail.summ)
                }
                for detail in await bill.details_in_bill.all().prefetch_related("service")
            ]
        }
    }


async def build_act_context(act: Acts) -> dict:

    def legal_entity_to_dict(entity):
        return {
            "legal_entity_name": entity.legal_entity_name,
            "inn": entity.inn,
            "kpp": entity.kpp,
            "vat_rate": entity.vat_rate,
            "address": entity.address,
            "signer": entity.signer,
            "entity_type": getattr(entity.entity_type, "status_name", None)
        }

    return {
        "act": {
            "act_id": str(act.act_id),
            "act_number": act.act_number,
            "act_date": format_date(act.act_date),
            "contract": {
                "contract_id": str(act.contract.contract_id),
                "contract_name": act.contract.contract_name,
                "contract_date": format_date(act.contract.contract_date),
                "comment": act.contract.comment,
                "buyer": legal_entity_to_dict(act.contract.buyer),
                "seller": legal_entity_to_dict(act.contract.seller),
                "status": getattr(act.contract.status, "status_name", None)
            },
            "details": [
                {
                    "service": {
                        "service_id": str(detail.service.service_id),
                        "service_name": detail.service.service_name
                    },
                    "quantity": float(detail.quantity),
                    "summ": float(detail.summ)
                }
                for detail in await act.details_in_act.all().prefetch_related("service")
            ]
        }
    }
