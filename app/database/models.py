import uuid
from fastapi import BackgroundTasks
import bcrypt
from tortoise.models import Model
from tortoise import fields


# Списки

class LegalEntityType(Model):
    legal_entity_type_id = fields.CharField(
        pk=True, max_length=255)  # Исправлено на UUID
    # Добавил уникальность
    entity_name = fields.CharField(max_length=255)

    class Meta:
        table = "legal_entity_types"


class UserRole(Model):
    role_id = fields.CharField(max_length=255, pk=True)
    role_name = fields.CharField(max_length=255)

    class Meta:
        table = "user_roles"


class ContractStatus(Model):
    contract_status_id = fields.CharField(max_length=255, pk=True)
    status_name = fields.CharField(max_length=255)

    class Meta:
        table = "contract_statuses"

# Полноценные модели


async def create_user(user_name: str, password: str, full_name: str, position: str):
    # Хэшируем пароль
    hashed_password = bcrypt.hashpw(
        password.encode(), bcrypt.gensalt()).decode()
    user = await User.create(user_name=user_name, password_hash=hashed_password, position=position, full_name=full_name)
    return user


class User(Model):
    user_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user_name = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)
    full_name = fields.CharField(max_length=255)
    position = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "users"

    async def check_password(self, password: str):
        return await BackgroundTasks().add_task(
            bcrypt.checkpw, password.encode(), self.password_hash.encode()
        )


class Company(Model):
    company_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    company_name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)

    class Meta:
        table = "companies"


class UserCompanyRelation(Model):
    user_company_id = fields.UUIDField(
        pk=True, default=uuid.uuid4)
    company = fields.ForeignKeyField(
        "models.Company", related_name="user_company_relations")
    user = fields.ForeignKeyField(
        "models.User", related_name="user_company_relations")
    role = fields.ForeignKeyField(
        "models.UserRole", related_name="user_company_relations")

    class Meta:
        table = "user_to_company_relations"


class LegalEntity(Model):
    legal_entity_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    legal_entity_name = fields.CharField(max_length=255)
    inn = fields.CharField(max_length=12, unique=True)
    # КПП не всегда есть (ИП его не имеют)
    kpp = fields.CharField(max_length=9, null=True)
    vat_rate = fields.IntField()
    address = fields.CharField(max_length=255)
    entity_type = fields.ForeignKeyField(
        "models.LegalEntityType", related_name="entities"
    )  # Указал правильную связь
    signer = fields.CharField(max_length=255, null=True)
    company = fields.ForeignKeyField(
        "models.Company", related_name="entities"
    )  # Добавил `on_delete`
    description = fields.TextField(null=True)

    class Meta:
        table = "legal_entities"


class Contract(Model):
    contract_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    contract_name = fields.CharField(max_length=255)
    contract_date = fields.BigIntField()
    buyer = fields.ForeignKeyField(
        "models.LegalEntity", related_name="contract_buyer")
    seller = fields.ForeignKeyField(
        "models.LegalEntity", related_name="contract_seller")
    comment = fields.TextField(null=True)
    file = fields.CharField(max_length=2083, null=True)
    status = fields.ForeignKeyField(
        "models.ContractStatus", related_name="contracts")

    class Meta:
        table = "contracts"


class BankAccount(Model):
    bank_account_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    account_number = fields.CharField(max_length=20)
    bank_name = fields.CharField(max_length=255)
    bank_bic = fields.CharField(max_length=9)
    bank_corr_account = fields.CharField(max_length=20)
    legal_entity = fields.ForeignKeyField(
        "models.LegalEntity", related_name="bank_accounts")

    class Meta:
        table = "bank_accounts"


class Acts(Model):
    act_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    act_number = fields.CharField(max_length=255)
    act_date = fields.BigIntField()
    contract = fields.ForeignKeyField(
        "models.Contract", related_name="acts",  on_delete=fields.CASCADE)

    class Meta:
        table = "acts"


class Bills(Model):
    bill_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    bank_account = fields.ForeignKeyField(
        "models.BankAccount", related_name="bills")
    bill_number = fields.CharField(max_length=255)
    bill_date = fields.BigIntField()
    contract = fields.ForeignKeyField("models.Contract", related_name="bills")

    class Meta:
        table = "bills"


class Service(Model):
    service_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    service_name = fields.CharField(max_length=255)

    class Meta:
        table = "services"


class BillDetails(Model):
    bill_detail_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    bill = fields.ForeignKeyField(
        "models.Bills", related_name="details_in_bill")
    service = fields.ForeignKeyField(
        "models.Service", related_name="services_in_bill")
    quantity = fields.DecimalField(max_digits=8, decimal_places=3)
    summ = fields.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        table = "bill_details"


class ActDetails(Model):
    act_detail_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    act = fields.ForeignKeyField("models.Acts", related_name="details_in_act")
    service = fields.ForeignKeyField(
        "models.Service", related_name="services_in_act")
    quantity = fields.DecimalField(max_digits=8, decimal_places=3)
    summ = fields.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        table = "act_details"
