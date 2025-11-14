import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.configs import db
from app.configs import logging as logging_module
from app.configs import settings
from app.repositories.calc_result import make_calc_result_repository
from app.routers.calc import make_calc_router
from app.services.calc import make_calc_service

logging_module.configure_logging(
    level=getattr(logging, settings.APP_LOG_LEVEL.upper(), logging.INFO)
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.async_engine = create_async_engine(
        settings.DATABASE_DSN,
        echo=True,
        pool_size=settings.POSTGRES_POOL_SIZE,
        max_overflow=settings.POSTGRES_MAX_OVERFLOW,
        pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
        pool_recycle=settings.POSTGRES_POOL_RECYCLE,
        pool_pre_ping=True,
        connect_args={"server_settings": {"search_path": settings.POSTGRES_SCHEMA}},
    )
    db.async_session_factory = async_sessionmaker(
        bind=db.async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    session_manager = db.make_session_manager(
        session_factory=db.async_session_factory,
        session_ctx=db.async_session_ctx,
    )
    transaction = db.make_transaction_decorator(session_manager)
    calc_repo = make_calc_result_repository(session_manager)
    calc_service = make_calc_service(calc_repo)
    calc_router = make_calc_router(
        calc_service=calc_service,
        transaction=transaction,
    )
    app.include_router(calc_router)

    yield

    await db.async_engine.dispose()


app = FastAPI(lifespan=lifespan, title=settings.APP_TITLE)


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level=settings.APP_LOG_LEVEL.lower(),
    )
