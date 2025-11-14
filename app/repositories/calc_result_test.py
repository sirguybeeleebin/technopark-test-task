from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.calc_result import make_calc_result_repository
from app.repositories.models.calc_result import CalcResult


@pytest.mark.asyncio
async def test_insert_calc_result_mocked():
    # Мокнутый объект CalcResult
    fake_row = CalcResult(id=1, total_cost_rub=Decimal("123.45"))

    # Мокнутый результат execute
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = fake_row

    # Мокнутая сессия
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_execute_result
    mock_session.commit.return_value = None
    mock_session.flush.return_value = None
    mock_session.rollback.return_value = None

    # Мокнутый движок
    mock_engine = MagicMock()
    mock_engine.get_session_from_ctx.return_value = None
    # Здесь важно возвращать сессию **не awaitable**
    mock_engine.get_session.return_value = mock_session

    # Репозиторий
    repo = make_calc_result_repository(mock_engine)

    # Вставка через репозиторий
    result = await repo.insert(total_cost_rub=Decimal("123.45"))

    # Проверяем результат
    assert result["id"] == 1
    assert result["total_cost_rub"] == Decimal("123.45")

    # Проверяем вызовы
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
