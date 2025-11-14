from datetime import datetime
from decimal import Decimal
from typing import Awaitable, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from starlette import status

from app.services.calc import CalcService


class Material(BaseModel):
    name: str = Field(
        ...,
        title="Название материала",
        description="Наименование материала",
        json_schema_extra={"example": "Сталь"},
    )
    qty: Decimal = Field(
        ...,
        title="Количество",
        description="Количество материала (дробное или целое, больше 0)",
        gt=0,
        json_schema_extra={"example": 12.3},
    )
    price_rub: Decimal = Field(
        ...,
        title="Цена в рублях",
        description="Цена за единицу материала в рублях (больше 0)",
        gt=0,
        json_schema_extra={"example": 54.5},
    )


class CalcRequest(BaseModel):
    materials: list[Material] = Field(
        ...,
        title="Список материалов",
        description="Список материалов для расчета стоимости",
        json_schema_extra={
            "example": [{"name": "Сталь", "qty": 12.3, "price_rub": 54.5}]
        },
    )

    @field_validator("materials")
    @classmethod
    def validate_materials_not_empty(cls, v):
        if not v:
            raise ValueError("Должен быть хотя бы один материал")
        return v


class CalcResponse(BaseModel):
    id: int = Field(
        ...,
        title="ID записи",
        description="Уникальный идентификатор записи в базе данных",
        json_schema_extra={"example": 1},
    )
    total_cost_rub: Decimal = Field(
        ...,
        title="Общая стоимость",
        description="Суммарная стоимость всех материалов в рублях",
        json_schema_extra={"example": 2505.0},
    )
    created_at: datetime = Field(
        ...,
        title="Дата создания",
        description="Время создания записи в базе данных",
        json_schema_extra={"example": "2025-11-14T12:00:00Z"},
    )


def make_calc_router(
    *,
    calc_service: CalcService,
    transaction: Callable[[Callable[..., Awaitable]], Callable[..., Awaitable]],
) -> APIRouter:
    router = APIRouter()

    @router.post("/calc")
    @transaction
    async def calc(req: CalcRequest) -> CalcResponse:
        try:
            materials_data = [m.model_dump() for m in req.materials]
            result = await calc_service.calculate_and_save(materials_data)
            return CalcResponse(**result)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Внутренняя ошибка сервиса",
            )

    return router
