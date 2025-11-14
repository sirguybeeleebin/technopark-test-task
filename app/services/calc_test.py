from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.repositories.calc_result import CalcResultRepository
from app.services.calc import CalcService


@pytest.mark.asyncio
async def test_calculate_and_save():
    mock_repo = AsyncMock(spec=CalcResultRepository)
    mock_repo.insert.return_value = {"id": 1, "total_cost_rub": Decimal("200.0")}

    service = CalcService(calc_result_repository=mock_repo)

    materials = [
        {"qty": 2, "price_rub": 50},
        {"qty": 1, "price_rub": 100},
    ]

    result = await service.calculate_and_save(materials)

    mock_repo.insert.assert_awaited_once_with(total_cost_rub=200)
    assert result == {"id": 1, "total_cost_rub": Decimal("200.0")}


@pytest.mark.asyncio
async def test_calculate_and_save_empty_materials():
    mock_repo = AsyncMock(spec=CalcResultRepository)
    mock_repo.insert.return_value = {"id": 1, "total_cost_rub": Decimal("0.0")}

    service = CalcService(calc_result_repository=mock_repo)

    result = await service.calculate_and_save([])

    mock_repo.insert.assert_awaited_once_with(total_cost_rub=0)
    assert result == {"id": 1, "total_cost_rub": Decimal("0.0")}
