from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.calc_result import make_calc_result_repository
from app.repositories.models.calc_result import CalcResult


@pytest.mark.asyncio
async def test_insert_calc_result_mocked():
    # Создаем мокнутую сессию
    mock_session = AsyncMock()
    fake_row = CalcResult(id=1, total_cost_rub=Decimal("123.45"))

    # Настраиваем execute, чтобы возвращать объект с async scalar_one_or_none
    mock_execute_result = AsyncMock()
    mock_execute_result.scalar_one_or_none.return_value = fake_row  # Важно: без await
    mock_session.execute.return_value = mock_execute_result
    mock_session.flush.return_value = AsyncMock()  # flush - async

    # Мокнутый движок
    mock_engine = MagicMock()
    mock_engine.get_session.return_value = mock_session

    # Репозиторий
    repo = make_calc_result_repository(mock_engine)

    # Вставка через репозиторий
    result = await repo.insert(total_cost_rub=Decimal("123.45"))

    # Проверяем результат
    assert result["id"] == 1
    assert result["total_cost_rub"] == Decimal("123.45")

    # Проверяем вызовы
    mock_session.execute.assert_called()
    mock_session.flush.assert_called()
