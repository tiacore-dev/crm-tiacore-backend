import uuid
import bcrypt
from tortoise.models import Model
from tortoise import fields


# Списки

class LegalEntityType(Model):
    legal_entity_type_id = fields.CharField(
        pk=True, max_length=255)
    entity_name = fields.CharField(max_length=255)

    class Meta:
        table = "legal_entity_types"


class UserRole(Model):

    role_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    role_name = fields.CharField(max_length=50, unique=True)
    role_system_name = fields.CharField(max_length=50, null=True, unique=True)

    def __repr__(self):
        return f"<UserRole(role_id={self.role_id}, role_name='{self.role_name}')>"

    class Meta:
        table = "user_roles"


class RolePermissionRelation(Model):
    role_permission_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    role = fields.ForeignKeyField(
        "models.UserRole", related_name="role_permission_relations",
        on_delete=fields.CASCADE)
    permission = fields.ForeignKeyField(
        "models.Permissions", related_name="role_permission_relations",
        on_delete=fields.CASCADE)

    class Meta:
        table = "role_permission_relations"


class Permissions(Model):
    permission_id = fields.CharField(max_length=255, pk=True)
    permission_name = fields.CharField(max_length=255)
    comment = fields.CharField(max_length=255, null=True)

    def __repr__(self):
        return f"<Permissions(permission_id={self.permission_id}, permission_name={self.permission_name})>"

    class Meta:
        table = "permissions"


class ContractStatus(Model):
    contract_status_id = fields.CharField(max_length=255, pk=True)
    status_name = fields.CharField(max_length=255)

    class Meta:
        table = "contract_statuses"


async def create_user(email: str, password: str, full_name: str, position: str):
    # Хэшируем пароль
    hashed_password = bcrypt.hashpw(
        password.encode(), bcrypt.gensalt()).decode()
    user = await User.create(email=email, password_hash=hashed_password, position=position, full_name=full_name)
    return user


class User(Model):
    user_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)
    full_name = fields.CharField(max_length=255)
    position = fields.CharField(max_length=255, null=True)
    is_superadmin = fields.BooleanField(default=False)

    class Meta:
        table = "users"

    def check_password(self, password: str):
        if not self.password_hash:
            return False  # Если пароль отсутствует в БД, всегда возвращаем False

        return bcrypt.checkpw(password.encode(), self.password_hash.encode())


class Company(Model):
    company_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    company_name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)

    class Meta:
        table = "companies"


class UserCompanyRelation(Model):
    user_company_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    company = fields.ForeignKeyField(
        "models.Company",
        related_name="user_company_relations",
        on_delete=fields.CASCADE
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="user_company_relations",
        on_delete=fields.CASCADE
    )
    role = fields.ForeignKeyField(
        "models.UserRole",
        related_name="user_company_relations",
        on_delete=fields.CASCADE
    )

    class Meta:
        table = "user_to_company_relations"


class EntityCompanyRelation(Model):
    entity_company_relation_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    company = fields.ForeignKeyField(
        "models.Company", related_name="entity_company_relations",
        on_delete=fields.CASCADE)
    legal_entity = fields.ForeignKeyField(
        "models.LegalEntity", related_name="entity_company_relations", on_delete=fields.CASCADE)
    relation_type = fields.CharField(max_length=10)
    description = fields.TextField(null=True)

    class Meta:
        table = "entity_company_relations"


class LegalEntity(Model):
    legal_entity_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    legal_entity_name = fields.CharField(max_length=255)
    inn = fields.CharField(max_length=12)
    kpp = fields.CharField(max_length=9, null=True)
    # от 0 до ста и может не передаваться
    vat_rate = fields.IntField(default=0)
    address = fields.CharField(max_length=255, null=True)
    entity_type = fields.ForeignKeyField(
        "models.LegalEntityType", related_name="entities", null=True
    )
    signer = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "legal_entities"
        unique_together = (("inn", "kpp"),)


class Contract(Model):
    contract_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    contract_name = fields.CharField(max_length=255)
    contract_date = fields.BigIntField()
    buyer = fields.ForeignKeyField(
        "models.LegalEntity", related_name="contract_buyer")
    seller = fields.ForeignKeyField(
        "models.LegalEntity", related_name="contract_seller")
    comment = fields.TextField(null=True)
    s3_key = fields.CharField(max_length=255, null=True)
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
        "models.Contract", related_name="acts", null=True)
    buyer = fields.ForeignKeyField(
        "models.LegalEntity", related_name="act_buyer")
    seller = fields.ForeignKeyField(
        "models.LegalEntity", related_name="act_seller")

    class Meta:
        table = "acts"


class Bills(Model):
    bill_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    bank_account = fields.ForeignKeyField(
        "models.BankAccount", related_name="bills")
    bill_number = fields.CharField(max_length=255)
    bill_date = fields.BigIntField()
    contract = fields.ForeignKeyField(
        "models.Contract", related_name="bills", null=True)
    buyer = fields.ForeignKeyField(
        "models.LegalEntity", related_name="bill_buyer")
    seller = fields.ForeignKeyField(
        "models.LegalEntity", related_name="bill_seller")

    class Meta:
        table = "bills"


class Service(Model):
    service_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    service_name = fields.CharField(max_length=255)
    company = fields.ForeignKeyField("models.Company", related_name="services")

    class Meta:
        table = "services"


class BillDetails(Model):
    bill_detail_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    bill = fields.ForeignKeyField(
        "models.Bills", related_name="details_in_bill",
        on_delete=fields.CASCADE)
    service = fields.ForeignKeyField(
        "models.Service", related_name="services_in_bill")
    quantity = fields.DecimalField(max_digits=8, decimal_places=3)
    summ = fields.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        table = "bill_details"


class ActDetails(Model):
    act_detail_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    act = fields.ForeignKeyField("models.Acts", related_name="details_in_act",
                                 on_delete=fields.CASCADE)
    service = fields.ForeignKeyField(
        "models.Service", related_name="services_in_act")
    quantity = fields.DecimalField(max_digits=8, decimal_places=3)
    summ = fields.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        table = "act_details"


class Templates(Model):
    template_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    template_name = fields.CharField(max_length=255)
    company = fields.ForeignKeyField(
        "models.Company", related_name="templates"
    )
    description = fields.TextField(null=True)
    entity = fields.CharField(max_length=50)
    s3_key = fields.CharField(max_length=255)

    class Meta:
        table = "templates"
