from loguru import logger
from tortoise import Tortoise
from tortoise.transactions import in_transaction


async def drop_all_tables():
    conn = Tortoise.get_connection("default")
    tables = await conn.execute_query_dict("""
        SELECT tablename FROM pg_tables WHERE schemaname = 'public';
    """)
    async with in_transaction() as tx:
        for table in tables:
            await tx.execute_query(
                f'DROP TABLE IF EXISTS "{table["tablename"]}" CASCADE;'
            )


async def create_test_data():
    from app.database.models import ContractStatus

    try:
        await ContractStatus.get_or_create(id="active", name="Активен")
        await ContractStatus.get_or_create(id="waiting", name="Ожидание")
        await ContractStatus.get_or_create(id="completed", name="Завершен")
        logger.info("Данные статусов контрактов успешно созданы")
    except Exception as e:
        print(f"Exception: {e}")
