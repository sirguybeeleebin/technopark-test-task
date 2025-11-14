from decimal import Decimal
from unittest.mock import AsyncMock

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.routers.calc import make_calc_router
from app.services.calc import CalcService


def test_calc_endpoint_success():
    mock_service = AsyncMock(spec=CalcService)
    mock_service.calculate_and_save.return_value = {
        "id": 1,
        "total_cost_rub": Decimal("2505.0"),
        "created_at": "2025-11-14T12:00:00Z",
    }

    def dummy_transaction(func):
        return func

    router = make_calc_router(calc_service=mock_service, transaction=dummy_transaction)

    app = FastAPI()
    app.include_router(router)

    payload = {
        "materials": [
            {"name": "Сталь", "qty": 10, "price_rub": 100},
            {"name": "Медь", "qty": 5, "price_rub": 101},
        ]
    }

    with TestClient(app) as client:
        response = client.post("/calc", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 1
    assert str(data["total_cost_rub"]) == "2505.0"
    assert data["created_at"] == "2025-11-14T12:00:00Z"
    mock_service.calculate_and_save.assert_awaited_once_with(
        [
            {"name": "Сталь", "qty": 10, "price_rub": 100},
            {"name": "Медь", "qty": 5, "price_rub": 101},
        ]
    )


def test_calc_endpoint_empty_materials():
    mock_service = AsyncMock(spec=CalcService)

    def dummy_transaction(func):
        return func

    router = make_calc_router(calc_service=mock_service, transaction=dummy_transaction)

    app = FastAPI()
    app.include_router(router)

    payload = {"materials": []}

    with TestClient(app) as client:
        response = client.post("/calc", json=payload)

    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    )  # Pydantic validation
