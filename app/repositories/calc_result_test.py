from contextlib import asynccontextmanager
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.calc_result import CalcResultRepository


@pytest.mark.asyncio
async def test_insert_returns_dict():
    mock_row = SimpleNamespace(id=1, total_cost_rub=Decimal("123.45"))
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one.return_value = mock_row
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_execute_result

    class DummySessionManager:
        @asynccontextmanager
        async def get_session(self):
            yield mock_session

    repo = CalcResultRepository(DummySessionManager())
    result = await repo.insert(total_cost_rub=Decimal("123.45"))

    mock_session.execute.assert_awaited_once()
    mock_execute_result.scalar_one.assert_called_once()
    assert result["id"] == 1
    assert result["total_cost_rub"] == Decimal("123.45")
