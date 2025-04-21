import os
from dotenv import load_dotenv
from app import create_app

load_dotenv()

# Порт и биндинг
PORT = 8000
PASSWORD = os.getenv('PASSWORD')
CONFIG_NAME = os.getenv('CONFIG_NAME')


async def create_admin_user():
    from app.database.models import create_user, User
    # Проверяем, существует ли пользователь "admin"
    admin = await User.filter(username="admin").first()
    if not admin:
        await create_user(username="admin", password=PASSWORD, position='admin', full_name='Поликанова Виктория Сергеевна')


async def create_test_data():
    from app.database.models import ContractStatus, LegalEntityType, UserRole
    try:
        await UserRole.create(role_name="Администратор", role_system_name="admin")
        await UserRole.create(role_name="Пользователь", role_system_name="user")
        await LegalEntityType.create(legal_entity_type_id="ip", entity_name="Индивидуальный предприниматель")
        await LegalEntityType.create(legal_entity_type_id="organization", entity_name="Организация")
        await ContractStatus.create(contract_status_id="active", status_name="Активен")
        await ContractStatus.create(contract_status_id="waiting", status_name="Ожидание")
    except Exception as e:
        print(f"Exception: {e}")

app = create_app(config_name=CONFIG_NAME)


@app.on_event("startup")
async def startup_event():
    # Создаем администратора при запуске
    await create_admin_user()
    await create_test_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(PORT), reload=True)
