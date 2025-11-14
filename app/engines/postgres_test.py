import logging

import pytest
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer

from app.engines.postgres import PostgresEngine

# Настраиваем логирование для тестов
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_postgres_engine_connect_and_ping():
    log.info("Запуск контейнера Postgres")
    with PostgresContainer("postgres:15") as pg:
        dsn = pg.get_connection_url().replace("postgresql+psycopg2://", "postgresql+asyncpg://")
        log.info(f"DSN для asyncpg: {dsn}")
        engine = PostgresEngine(dsn=dsn, schema="public")

        log.info("Подключение к базе данных")
        await engine.connect()
        ping_result = await engine.ping()
        log.info(f"Результат пинга: {ping_result}")
        assert ping_result is True

        log.info("Получение сессии и выполнение SELECT 1")
        session = engine.get_session()
        async with session.begin():
            result = await session.execute(text("SELECT 1"))
            value = result.scalar_one()
            log.info(f"Результат запроса SELECT 1: {value}")
            assert value == 1

        log.info("Проверка транзакции через декоратор")
        called = False

        async def dummy_transaction():
            nonlocal called
            called = True
            s = engine.get_session()
            result = await s.execute(text("SELECT 1"))
            val = result.scalar_one()
            log.info(f"Внутри транзакции, SELECT 1 = {val}")
            return val

        wrapped = engine.transaction(dummy_transaction)
        val = await wrapped()
        log.info(f"Результат транзакции: {val}, called={called}")
        assert val == 1
        assert called is True

        log.info("Отключение от базы данных")
        await engine.disconnect()
        log.info("Тест завершён")
