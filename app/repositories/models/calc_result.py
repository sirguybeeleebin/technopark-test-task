from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.repositories.models.base import Base


class CalcResult(Base):
    __tablename__ = "calc_results"
    __table_args__ = {"schema": "calc_schema"}  

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    total_cost_rub: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
