import logging
from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Coroutine

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

log = logging.getLogger(__name__)

async_engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None

async_session_ctx: ContextVar[AsyncSession | None] = ContextVar(
    "async_db_session",
    default=None,
)


class SessionManager:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        session_ctx: ContextVar[AsyncSession | None],
    ):
        self.session_factory = session_factory
        self.session_ctx = session_ctx

    @asynccontextmanager
    async def get_session(self):
        session = self.session_ctx.get()
        new = session is None

        if new:
            session = self.session_factory()
            token = self.session_ctx.set(session)
            log.info("Создана новая сессия")
        else:
            token = None
            log.info("Используется существующая сессия из контекста")

        try:
            yield session
            if new:
                await session.commit()
                log.info("Сессия успешно закоммичена")
        except Exception as e:
            if new:
                await session.rollback()
                log.info(f"Сессия откатилась из-за ошибки: {e}")
            raise
        finally:
            if new:
                await session.close()
                self.session_ctx.reset(token)
                log.info("Сессия закрыта")


def make_session_manager(
    session_factory: async_sessionmaker[AsyncSession],
    session_ctx: ContextVar[AsyncSession | None],
) -> SessionManager:
    return SessionManager(
        session_factory=session_factory,
        session_ctx=session_ctx,
    )


def make_transaction_decorator(session_manager: SessionManager):
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            log.info(f"Начало транзакции для функции {func.__name__}")
            async with session_manager.get_session():
                result = await func(*args, **kwargs)
            log.info(f"Транзакция для функции {func.__name__} завершена")
            return result

        return wrapper

    return decorator
