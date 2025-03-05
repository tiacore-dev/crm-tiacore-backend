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
        await create_user(username="admin", password=PASSWORD, role='admin', full_name='Поликанова Виктория Сергеевна')


app = create_app()


@app.on_event("startup")
async def startup_event():
    # Создаем администратора при запуске
    await create_admin_user()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(PORT), reload=True)
