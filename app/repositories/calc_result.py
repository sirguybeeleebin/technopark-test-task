import logging
from decimal import Decimal

from sqlalchemy import insert

from app.configs.db import SessionManager
from app.repositories.models.calc_result import CalcResult

log = logging.getLogger(__name__)


class CalcResultRepository:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    async def insert(self, total_cost_rub: Decimal) -> dict:
        async with self.session_manager.get_session() as session:
            stmt = (
                insert(CalcResult)
                .values(total_cost_rub=total_cost_rub)
                .returning(CalcResult)
            )
            result = await session.execute(stmt)
            row: CalcResult = result.scalar_one()
            return row.__dict__


def make_calc_result_repository(
    session_manager: SessionManager,
) -> CalcResultRepository:
    return CalcResultRepository(session_manager=session_manager)
