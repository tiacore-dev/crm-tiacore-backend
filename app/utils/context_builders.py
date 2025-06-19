import datetime

from app.database.models import Acts, Bills


def format_date(timestamp: int) -> str:
    try:
        return datetime.datetime.fromtimestamp(int(timestamp)).strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return "–"


def flatten_context(obj, parent_key="", sep=".") -> dict:
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
            "entity_type": getattr(entity.entity_type, "status_name", None),
        }

    return {
        "bill": {
            "bill_id": str(bill.id),
            "bill_number": bill.number,
            "bill_date": format_date(bill.date),
            "contract": {
                "contract_id": str(bill.contract.id) if bill.contract else None,
                "contract_name": bill.contract.name if bill.contract else None,
                "contract_date": format_date(bill.contract.date)
                if bill.contract
                else None,
                "buyer": legal_entity_to_dict(bill.contract.buyer_id)
                if bill.contract
                else None,
                "seller": legal_entity_to_dict(bill.contract.seller_id)
                if bill.contract
                else None,
                "status": getattr(bill.contract.status, "status_name", None)
                if bill.contract
                else None,
            },
            "bank_account": {
                "account_number": bill.bank_account.number,
                "bank_name": bill.bank_account.bank_name,
                "bank_bic": bill.bank_account.bank_bic,
                "bank_corr_account": bill.bank_account.bank_corr_account,
                "legal_entity": legal_entity_to_dict(bill.bank_account.legal_entity_id),
            },
            "details": [
                {
                    "service": {
                        "service_name": detail.service.name,
                        "service_id": str(detail.service.id),
                    },
                    "quantity": float(detail.quantity),
                    "summ": float(detail.summ),
                }
                for detail in await bill.details_in_bill.all().prefetch_related(
                    "service"
                )
            ],
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
            "entity_type": getattr(entity.entity_type, "status_name", None),
        }

    return {
        "act": {
            "act_id": str(act.id),
            "act_number": act.number,
            "act_date": format_date(act.date),
            "contract": {
                "contract_id": str(act.contract.id) if act.contract else None,
                "contract_name": act.contract.name if act.contract else None,
                "contract_date": format_date(act.contract.date)
                if act.contract
                else None,
                "comment": act.contract.comment if act.contract else None,
                "buyer": legal_entity_to_dict(act.contract.buyer_id)
                if act.contract
                else None,
                "seller": legal_entity_to_dict(act.contract.seller_id)
                if act.contract
                else None,
                "status": getattr(act.contract.status, "status_name", None)
                if act.contract
                else None,
            },
            "details": [
                {
                    "service": {
                        "service_id": str(detail.service.id),
                        "service_name": detail.service.name,
                    },
                    "quantity": float(detail.quantity),
                    "summ": float(detail.summ),
                }
                for detail in await act.details_in_act.all().prefetch_related("service")
            ],
        }
    }
