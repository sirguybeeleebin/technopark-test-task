from contextvars import ContextVar
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.session_manager.session_manager import SessionManager


@pytest.mark.asyncio
async def test_get_session_creates_new_session_and_commits():
    session_mock = AsyncMock(spec=AsyncSession)
    session_factory = MagicMock(return_value=session_mock)
    ctx = ContextVar("session_ctx", default=None)

    manager = SessionManager(session_factory=session_factory, session_ctx=ctx)

    async with manager.get_session() as session:
        assert session is session_mock
        session_mock.commit.assert_not_called()
        session_mock.rollback.assert_not_called()
        session_mock.close.assert_not_called()

    session_mock.commit.assert_awaited_once()
    session_mock.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_uses_existing_session():
    session_mock = AsyncMock(spec=AsyncSession)
    ctx = ContextVar("session_ctx")
    token = ctx.set(session_mock)

    manager = SessionManager(session_factory=None, session_ctx=ctx)

    async with manager.get_session() as session:
        assert session is session_mock
        session.commit.assert_not_called()
        session.close.assert_not_called()

    ctx.reset(token)


@pytest.mark.asyncio
async def test_transaction_method_commits():
    session_mock = AsyncMock(spec=AsyncSession)
    session_factory = MagicMock(return_value=session_mock)
    ctx = ContextVar("session_ctx", default=None)

    manager = SessionManager(session_factory=session_factory, session_ctx=ctx)
    transaction_decorator = manager.transaction

    called = {}

    @transaction_decorator
    async def func(x):
        called["x"] = x
        return x * 2

    result = await func(5)
    assert result == 10
    assert called["x"] == 5
    session_mock.commit.assert_awaited_once()
    session_mock.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_transaction_method_rollbacks_on_exception():
    session_mock = AsyncMock(spec=AsyncSession)
    session_factory = MagicMock(return_value=session_mock)
    ctx = ContextVar("session_ctx", default=None)

    manager = SessionManager(session_factory=session_factory, session_ctx=ctx)
    transaction_decorator = manager.transaction

    @transaction_decorator
    async def func():
        raise ValueError("fail")

    with pytest.raises(ValueError):
        await func()

    session_mock.rollback.assert_awaited_once()
    session_mock.close.assert_awaited_once()
