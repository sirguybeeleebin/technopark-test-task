import logging
from decimal import Decimal

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.postgres import PostgresEngine
from app.repositories.models.calc_result import CalcResult

log = logging.getLogger(__name__)


class CalcResultRepository:
    def __init__(self, postgres_engine: PostgresEngine) -> None:
        self._postgres_engine = postgres_engine

    async def insert(self, *, total_cost_rub: Decimal) -> dict:        
        session: AsyncSession | None = self._postgres_engine.get_session_from_ctx()
        new_session = False

        if session is None:
            session = self._postgres_engine.get_session()
            new_session = True

        try:
            stmt = insert(CalcResult).values(total_cost_rub=total_cost_rub).returning(CalcResult)
            result = await session.execute(stmt)
            row: CalcResult | None = result.scalar_one_or_none()
            if row is None:
                raise RuntimeError("Не удалось сохранить запись в базе данных")
            await session.commit()   if new_session else await session.flush()     

            log.info(f"Результат сохранён: id={row.id}, total_cost_rub={row.total_cost_rub}")
            return {
                "id": row.id,
                "total_cost_rub": row.total_cost_rub,
                "created_at": row.created_at
            }

        except Exception as e:
            log.error(f"Ошибка при insert: {e}")
            if new_session:
                await session.rollback()
            raise


def make_calc_result_repository(postgres_engine: PostgresEngine) -> CalcResultRepository:
    return CalcResultRepository(postgres_engine=postgres_engine)
