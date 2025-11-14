import json
import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from logging import config as logging_config

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.repositories.calc_result import make_calc_result_repository
from app.routers.calc import make_calc_router
from app.services.calc import make_calc_service
from app.session_manager.session_manager import make_session_manager

load_dotenv()

APP_TITLE = os.getenv("APP_TITLE", "Калькулятор стоимости")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
APP_DEBUG = os.getenv("APP_DEBUG", "False").lower() in ("true", "1")
APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").upper()

POSTGRES_HOST = os.getenv("DOCKER_POSTGRES_HOST") or os.getenv(
    "POSTGRES_HOST", "localhost"
)
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "calc_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "calc_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "calc_password")
POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "calc_schema")

DATABASE_DSN = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

POSTGRES_POOL_SIZE = int(os.getenv("POSTGRES_POOL_SIZE", 5))
POSTGRES_MAX_OVERFLOW = int(os.getenv("POSTGRES_MAX_OVERFLOW", 10))
POSTGRES_POOL_TIMEOUT = int(os.getenv("POSTGRES_POOL_TIMEOUT", 30))
POSTGRES_POOL_RECYCLE = int(os.getenv("POSTGRES_POOL_RECYCLE", 1800))

async_session_ctx: ContextVar[AsyncSession | None] = ContextVar(
    "async_session_ctx", default=None
)
trace_id_ctx: ContextVar[str] = ContextVar("trace_id_ctx", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        trace_id = trace_id_ctx.get()
        if not trace_id:
            trace_id = str(uuid.uuid4())
        return json.dumps(
            {
                "trace_id": trace_id,
                "timestamp": datetime.fromtimestamp(
                    record.created, tz=timezone.utc
                ).isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "source": f"{record.pathname}:{record.lineno}",
            },
            ensure_ascii=False,
        )


logging_config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": APP_LOG_LEVEL,
                "stream": sys.stdout,
            }
        },
        "root": {"handlers": ["stdout"], "level": APP_LOG_LEVEL},
    }
)


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = str(uuid.uuid4())
        token = trace_id_ctx.set(trace_id)
        try:
            response = await call_next(request)
            return response
        finally:
            trace_id_ctx.reset(token)


log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Инициализация подключения к базе данных...")
    async_engine = create_async_engine(
        DATABASE_DSN,
        echo=True,
        pool_size=POSTGRES_POOL_SIZE,
        max_overflow=POSTGRES_MAX_OVERFLOW,
        pool_timeout=POSTGRES_POOL_TIMEOUT,
        pool_recycle=POSTGRES_POOL_RECYCLE,
        pool_pre_ping=True,
        connect_args={"server_settings": {"search_path": POSTGRES_SCHEMA}},
    )
    log.info("Подключение к базе данных создано")

    async_session_factory = async_sessionmaker(
        bind=async_engine, expire_on_commit=False, class_=AsyncSession
    )
    log.info("Фабрика сессий SQLAlchemy создана")

    session_manager = make_session_manager(
        session_factory=async_session_factory,
        session_ctx=async_session_ctx,
    )
    log.info("Менеджер сессий создан")

    calc_repo = make_calc_result_repository(session_manager=session_manager)
    log.info("Репозиторий CalcResultRepository создан")

    calc_service = make_calc_service(calc_repo)
    log.info("Сервис CalcService создан")

    calc_router = make_calc_router(
        calc_service=calc_service,
        transaction=session_manager.transaction,
    )
    app.include_router(calc_router)
    log.info("Роутер calc зарегистрирован")

    yield

    log.info("Закрытие подключения к базе данных...")
    await async_engine.dispose()
    log.info("Подключение к базе данных закрыто")


app = FastAPI(lifespan=lifespan, title=APP_TITLE)
app.add_middleware(TraceIdMiddleware)


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    log.exception("Непредвиденная ошибка: %s", exc)
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"},
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_DEBUG,
        log_level=APP_LOG_LEVEL.lower(),
    )
