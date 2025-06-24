import uuid

from tortoise import fields
from tortoise.fields.relational import ReverseRelation
from tortoise.models import Model


class ContractStatus(Model):
    id = fields.CharField(max_length=255, pk=True)
    name = fields.CharField(max_length=255)

    class Meta:
        table = "contract_statuses"


class EntityCompanyRelation(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    company_id = fields.UUIDField()
    legal_entity_id = fields.UUIDField()
    relation_type = fields.CharField(max_length=10)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "entity_company_relations"


class Contract(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=255)
    date = fields.BigIntField()
    buyer_id = fields.UUIDField()
    seller_id = fields.UUIDField()
    comment = fields.TextField(null=True)
    s3_key = fields.CharField(max_length=255, null=True)
    status = fields.ForeignKeyField("models.ContractStatus", related_name="contracts")
    company_id = fields.UUIDField()

    class Meta:
        table = "contracts"


class BankAccount(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    number = fields.CharField(max_length=20)
    bank_name = fields.CharField(max_length=255)
    bank_bic = fields.CharField(max_length=9)
    bank_corr_account = fields.CharField(max_length=20)
    legal_entity_id = fields.UUIDField()

    class Meta:
        table = "bank_accounts"


class Acts(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    number = fields.CharField(max_length=255)
    date = fields.BigIntField()
    contract = fields.ForeignKeyField("models.Contract", related_name="acts", null=True)
    buyer_id = fields.UUIDField()
    seller_id = fields.UUIDField()
    company_id = fields.UUIDField()

    details_in_act: ReverseRelation["ActDetails"]

    class Meta:
        table = "acts"


class Bills(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    bank_account = fields.ForeignKeyField("models.BankAccount", related_name="bills")
    number = fields.CharField(max_length=255)
    date = fields.BigIntField()
    contract = fields.ForeignKeyField(
        "models.Contract", related_name="bills", null=True
    )
    buyer_id = fields.UUIDField()
    seller_id = fields.UUIDField()
    company_id = fields.UUIDField()

    details_in_bill: ReverseRelation["BillDetails"]

    class Meta:
        table = "bills"


class Service(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=255)
    company_id = fields.UUIDField()

    class Meta:
        table = "services"


class BillDetails(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    bill = fields.ForeignKeyField(
        "models.Bills", related_name="details_in_bill", on_delete=fields.CASCADE
    )
    service = fields.ForeignKeyField("models.Service", related_name="services_in_bill")
    quantity = fields.DecimalField(max_digits=8, decimal_places=3)
    summ = fields.DecimalField(max_digits=10, decimal_places=2)
    price = fields.DecimalField(max_digits=8, decimal_places=2)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "bill_details"


class ActDetails(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    act = fields.ForeignKeyField(
        "models.Acts", related_name="details_in_act", on_delete=fields.CASCADE
    )
    service = fields.ForeignKeyField("models.Service", related_name="services_in_act")
    quantity = fields.DecimalField(max_digits=8, decimal_places=3)
    summ = fields.DecimalField(max_digits=10, decimal_places=2)
    price = fields.DecimalField(max_digits=8, decimal_places=2)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "act_details"


class Templates(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=255)
    company_id = fields.UUIDField()
    description = fields.TextField(null=True)
    entity = fields.CharField(max_length=50)
    s3_key = fields.CharField(max_length=255)

    class Meta:
        table = "templates"
