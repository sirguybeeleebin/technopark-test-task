from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.repositories.calc_result import CalcResultRepository
from app.services.calc import CalculationService


@pytest.mark.asyncio
async def test_calculate_and_save_success():
    mock_calc_repo = AsyncMock(spec=CalcResultRepository)
    mock_calc_repo.insert.return_value = {
        "id": 1,
        "total_cost_rub": Decimal("123.45"),
        "created_at": datetime(2025, 11, 14, 12, 0)
    }

    calc_service = CalculationService(calc_result_repository=mock_calc_repo)

    materials = [
        {"name": "Steel", "qty": 2, "price_rub": Decimal("50.00")},
        {"name": "Plastic", "qty": 1, "price_rub": Decimal("23.45")}
    ]

    resp = await calc_service.calculate_and_save(materials)

    assert resp["id"] == 1
    assert resp["total_cost_rub"] == Decimal("123.45")
    assert resp["created_at"] == datetime(2025, 11, 14, 12, 0)
    mock_calc_repo.insert.assert_awaited_once_with(total_cost_rub=Decimal("123.45"))


@pytest.mark.asyncio
async def test_calculate_and_save_raises_internal_error():
    mock_calc_repo = AsyncMock(spec=CalcResultRepository)
    mock_calc_repo.insert.side_effect = Exception("DB error")

    calc_service = CalculationService(calc_result_repository=mock_calc_repo)

    materials = [
        {"name": "Copper", "qty": 1, "price_rub": Decimal("100.00")}
    ]

    with pytest.raises(Exception):
        await calc_service.calculate_and_save(materials)
    
    mock_calc_repo.insert.assert_awaited_once_with(total_cost_rub=Decimal("100.00"))
