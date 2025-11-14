from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.calc import make_calc_router
from app.services.calc import CalculationService


@pytest.mark.asyncio
async def test_calc_success():
    # Mock the service
    mock_calc_service = AsyncMock(spec=CalculationService)
    mock_calc_service.calculate_and_save.return_value = {
        "id": 1,
        "total_cost_rub": Decimal("123.45"),
        "created_at": datetime(2025, 11, 14, 12, 0)
    }

    # Dummy transaction decorator
    def dummy_transaction(func):
        return func

    # Create router and FastAPI app
    router = make_calc_router(calc_service=mock_calc_service, transaction=dummy_transaction)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    payload = {
        "materials": [
            {"name": "Steel", "qty": 2, "price_rub": 50.00},
            {"name": "Plastic", "qty": 1, "price_rub": 23.45}
        ]
    }

    response = client.post("/calc", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == 1
    # Convert to Decimal for correct comparison
    assert Decimal(data["total_cost_rub"]) == Decimal("123.45")
    assert data["created_at"] == "2025-11-14T12:00:00"

    # Mock called with Decimal values, because Pydantic parses JSON numbers into Decimals
    mock_calc_service.calculate_and_save.assert_awaited_once_with([
        {"name": "Steel", "qty": Decimal("2"), "price_rub": Decimal("50.0")},
        {"name": "Plastic", "qty": Decimal("1"), "price_rub": Decimal("23.45")}
    ])


@pytest.mark.asyncio
async def test_calc_failure():
    # Mock service raising exception
    mock_calc_service = AsyncMock(spec=CalculationService)
    mock_calc_service.calculate_and_save.side_effect = Exception("DB error")

    def dummy_transaction(func):
        return func

    router = make_calc_router(calc_service=mock_calc_service, transaction=dummy_transaction)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    payload = {
        "materials": [
            {"name": "Copper", "qty": 1, "price_rub": 100.0}
        ]
    }

    response = client.post("/calc", json=payload)
    assert response.status_code == 500
    assert response.json()["detail"] == "Внутренняя ошибка сервиса"

    mock_calc_service.calculate_and_save.assert_awaited_once_with([
        {"name": "Copper", "qty": Decimal("1"), "price_rub": Decimal("100.0")}
    ])
