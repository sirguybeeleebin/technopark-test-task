from contextvars import ContextVar
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.db import SessionManager, make_transaction_decorator


@pytest.mark.asyncio
async def test_get_session_commit():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.rollback = AsyncMock()

    mock_factory = MagicMock(return_value=mock_session)
    test_ctx = ContextVar("test_ctx", default=None)
    session_manager = SessionManager(mock_factory, test_ctx)

    async with session_manager.get_session() as session:
        assert session == mock_session

    mock_session.commit.assert_awaited_once()
    mock_session.close.assert_awaited_once()
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_get_session_rollback():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.rollback = AsyncMock()

    mock_factory = MagicMock(return_value=mock_session)
    test_ctx = ContextVar("test_ctx", default=None)
    session_manager = SessionManager(mock_factory, test_ctx)

    with pytest.raises(ValueError):
        async with session_manager.get_session() as _:
            raise ValueError("trigger rollback")

    mock_session.rollback.assert_awaited_once()
    mock_session.close.assert_awaited_once()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_transaction_decorator():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.rollback = AsyncMock()

    mock_factory = MagicMock(return_value=mock_session)
    test_ctx = ContextVar("test_ctx", default=None)
    session_manager = SessionManager(mock_factory, test_ctx)
    transaction = make_transaction_decorator(session_manager)

    called = {}

    @transaction
    async def sample_func(x):
        called["x"] = x
        return x * 2

    result = await sample_func(10)
    assert result == 20
    assert called["x"] == 10

    mock_session.commit.assert_awaited_once()
    mock_session.close.assert_awaited_once()
