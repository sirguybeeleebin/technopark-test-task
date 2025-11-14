import logging

from app.repositories.calc_result import CalcResultRepository

log = logging.getLogger(__name__)


class CalculationService:
    def __init__(self, *, calc_result_repository: CalcResultRepository):
        self._calc_result_repository = calc_result_repository

    async def calculate_and_save(self, materials: list[dict]) -> dict:
        total_cost = sum((m["qty"] * m["price_rub"] for m in materials))
        log.info(f"Начало расчета: total_cost={total_cost} для материалов {materials}")

        try:
            calc_result_data = await self._calc_result_repository.insert(total_cost_rub=total_cost)
            log.info(
                f"Результат расчета сохранен: id={calc_result_data['id']}, "
                f"total_cost_rub={calc_result_data['total_cost_rub']}"
            )
        except Exception as e:
            log.error(f"Ошибка при сохранении результата расчета: {e}")
            raise

        return calc_result_data
    

def make_calculation_service(calc_result_repository: CalcResultRepository) -> CalculationService:
    return CalculationService(calc_result_repository=calc_result_repository)
