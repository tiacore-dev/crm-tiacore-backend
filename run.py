import os
from dotenv import load_dotenv
from app import create_app

load_dotenv()

# Порт и биндинг
PORT = os.getenv('PORT', "5020")
PASSWORD = os.getenv('PASSWORD')


async def create_admin_user():
    from app.database.models import create_user, User
    # Проверяем, существует ли пользователь "admin"
    admin = await User.filter(username="admin").first()
    if not admin:
        await create_user(username="admin", password=PASSWORD, position='admin', full_name='Поликанова Виктория Сергеевна')


async def create_test_data():
    from app.database.models import ContractStatus, LegalEntityType, UserRole
    try:
        await LegalEntityType.create(legal_entity_type_id="adc", entity_name="Компания ABC")
        await LegalEntityType.create(legal_entity_type_id="xyz", entity_name="Компания XYZ")
        await UserRole.create(role_id="admin", role_name="Администратор")
        await UserRole.create(role_id="manager", role_name="Менеджер")
        await ContractStatus.create(contract_status_id="active", status_name="Активен")
        await ContractStatus.create(contract_status_id="waiting", status_name="Ожидание")
    except Exception as e:
        print(f"Exception: {e}")

app = create_app()


@app.on_event("startup")
async def startup_event():
    # Создаем администратора при запуске
    await create_admin_user()
    await create_test_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(PORT), reload=True)
