import uuid
import bcrypt
from tortoise.models import Model
from tortoise import fields


async def create_user(username: str, password: str, role: str, full_name: str):
    # Хэшируем пароль
    hashed_password = bcrypt.hashpw(
        password.encode(), bcrypt.gensalt()).decode()
    user = await User.create(username=username, password_hash=hashed_password, role=role, full_name=full_name)
    return user


class User(Model):
    user_id = fields.UUIDField(
        pk=True, default=uuid.uuid4)  # UUID как Primary Key
    username = fields.CharField(max_length=50, unique=True)
    password_hash = fields.CharField(max_length=255)
    role = fields.CharField(max_length=50)
    full_name = fields.CharField(max_length=50)

    class Meta:
        table = "users"

    def check_password(self, password):
        if self.password_hash:
            return bcrypt.checkpw(password.encode(), self.password_hash.encode())
        return False

from tortoise import Model, fields

MAX_VERSION_LENGTH = 255


class Aerich(Model):
    version = fields.CharField(max_length=MAX_VERSION_LENGTH)
    app = fields.CharField(max_length=20)

    class Meta:
        ordering = ["-id"]

