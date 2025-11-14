import logging
from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

log = logging.getLogger(__name__)


class SessionManager:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        session_ctx: ContextVar[AsyncSession | None],
    ):
        self.session_factory = session_factory
        self.session_ctx = session_ctx

    @asynccontextmanager
    async def get_session(self):
        parent = self.session_ctx.get()
        if parent is None:
            session = self.session_factory()
            log.info("Создана локальная сессия")
            try:
                yield session
                await session.commit()
                log.info("Локальная сессия: commit")
            except Exception as exc:
                await session.rollback()
                log.info("Локальная сессия: rollback из-за ошибки: %s", exc)
                raise
            finally:
                await session.close()
                log.info("Локальная сессия закрыта")
            return

        log.info("Используется существующая сессия из контекста")
        try:
            yield parent
        except Exception:
            raise

    def transaction(self, func: Any):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            log.info("Начало транзакции для функции %s", func.__name__)
            session = self.session_factory()
            token = self.session_ctx.set(session)

            try:
                result = await func(*args, **kwargs)
                await session.commit()
                log.info("Транзакционная сессия: commit")
                return result
            except Exception as exc:
                await session.rollback()
                log.info("Транзакционная сессия: rollback из-за ошибки: %s", exc)
                raise
            finally:
                await session.close()
                self.session_ctx.reset(token)
                log.info("Транзакционная сессия: закрыта, контекст сброшен")

        return wrapper


def make_session_manager(
    session_factory: async_sessionmaker[AsyncSession],
    session_ctx: ContextVar[AsyncSession | None],
) -> SessionManager:
    return SessionManager(
        session_factory=session_factory,
        session_ctx=session_ctx,
    )
