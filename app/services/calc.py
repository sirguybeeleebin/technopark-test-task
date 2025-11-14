from app.repositories.calc_result import CalcResultRepository


class CalcService:
    def __init__(self, *, calc_result_repository: CalcResultRepository):
        self._calc_result_repository = calc_result_repository

    async def calculate_and_save(self, materials: list[dict]) -> dict:
        return await self._calc_result_repository.insert(
            total_cost_rub=sum(m["qty"] * m["price_rub"] for m in materials),
        )


def make_calc_service(calc_result_repository: CalcResultRepository) -> CalcService:
    return CalcService(calc_result_repository=calc_result_repository)
