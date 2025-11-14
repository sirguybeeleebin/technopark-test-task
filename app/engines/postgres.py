import logging
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Coroutine

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

log = logging.getLogger(__name__)


class PostgresEngine:
    # Разрешённые параметры для create_async_engine
    _ALLOWED_ENGINE_KWARGS = {
        "echo",
        "pool_size",
        "max_overflow",
        "pool_timeout",
        "pool_recycle",
        "execution_options",
    }

    def __init__(self, dsn: str, schema: str | None = None):
        """
        dsn    — строка подключения (без options)
        schema — search_path, передаётся через server_settings для asyncpg
        """
        self._dsn = dsn
        self._schema = schema
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

        # ContextVar — чтобы не хранить сессии в глобальном состоянии
        self._session_ctx: ContextVar[AsyncSession | None] = ContextVar(
            "async_db_session", default=None
        )

    async def connect(self, **kwargs):
        if self._engine is None:
            try:
                # фильтруем только разрешённые параметры
                filtered_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k in self._ALLOWED_ENGINE_KWARGS
                }

                # добавляем correct asyncpg search_path
                connect_args = {}

                if self._schema:
                    connect_args["server_settings"] = {
                        "search_path": self._schema
                    }

                # создаём движок
                self._engine = create_async_engine(
                    self._dsn,
                    future=True,
                    connect_args=connect_args,    # <── добавлено
                    **filtered_kwargs
                )

                self._session_factory = async_sessionmaker(
                    self._engine,
                    expire_on_commit=False
                )

                log.info(
                    f"Подключение к базе данных установлено: {self._dsn} "
                    f"(schema={self._schema})"
                )

            except Exception as e:
                log.error(f"Не удалось подключиться к базе данных: {e}")
                raise

    async def disconnect(self):
        if self._engine:
            try:
                await self._engine.dispose()
                log.info("Соединение с базой данных закрыто")
            except Exception as e:
                log.error(f"Ошибка при закрытии соединения с БД: {e}")
                raise
            finally:
                self._engine = None
                self._session_factory = None

    async def ping(self) -> bool:
        if not self._engine:
            raise RuntimeError("Движок не инициализирован")

        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            log.info("Пинг к базе данных успешен")
            return True

        except Exception as e:
            log.error(f"Пинг к базе данных не удался: {e}")
            return False

    def get_session_from_ctx(self) -> AsyncSession | None:       
        return self._session_ctx.get()

    def get_session(self) -> AsyncSession:        
        if self._session_factory is None:
            raise RuntimeError("Фабрика сессий не инициализирована")
        return self._session_factory()

    def transaction(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]]
    ) -> Callable[..., Coroutine[Any, Any, Any]]:

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self._session_factory is None:
                raise RuntimeError("Фабрика сессий не инициализирована")
           
            session: AsyncSession = self._session_factory()
            token = self._session_ctx.set(session)
            log.info("Создана новая сессия и помещена в контекст для транзакции")

            try:
                result = await func(*args, **kwargs)
                await session.commit()
                log.info("Транзакция успешно завершена (commit)")
                return result

            except Exception:
                await session.rollback()
                log.exception("Ошибка в транзакции — выполнен rollback")
                raise

            finally:
                self._session_ctx.reset(token)
                await session.close()
                log.info("Сессия закрыта после транзакции и удалена из контекста")

        return wrapper


def make_postgres_engine(dsn: str, schema: str | None = None) -> PostgresEngine:
    return PostgresEngine(dsn, schema)
