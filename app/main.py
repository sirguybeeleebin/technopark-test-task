import argparse
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from logging import config as logging_config
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.calc import make_calc_router
from app.engines.postgres import make_postgres_engine
from app.repositories.calc_result import make_calc_result_repository
from app.services.calc import CalculationService

# ---------------------------
#   ARGPARSE + ENV LOADING
# ---------------------------

parser = argparse.ArgumentParser(description="FastAPI приложение с настраиваемым .env файлом")
parser.add_argument(
    "--env-file",
    type=str,
    default=".env",
    help="Путь к .env файлу для загрузки конфигурации",
)
args, _ = parser.parse_known_args()

env_path = Path(args.env_file)
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"Внимание: файл .env {env_path} не найден, используются переменные окружения по умолчанию")


# ---------------------------
#        APP CONFIG
# ---------------------------

APP_TITLE = os.getenv("APP_TITLE", "Калькулятор стоимости")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
APP_DEBUG = os.getenv("APP_DEBUG", "False").lower() in ("true", "1")
APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "info").lower()
APP_WORKERS = int(os.getenv("APP_WORKERS", 1))

POSTGRES_HOST = os.getenv("DOCKER_POSTGRES_HOST") or os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "calc_db")
POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "calc_schema")
POSTGRES_USER = os.getenv("POSTGRES_USER", "calc_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "calc_password")

POSTGRES_POOL_SIZE = int(os.getenv("POSTGRES_POOL_SIZE", 5))
POSTGRES_MAX_OVERFLOW = int(os.getenv("POSTGRES_MAX_OVERFLOW", 10))
POSTGRES_POOL_TIMEOUT = int(os.getenv("POSTGRES_POOL_TIMEOUT", 30))
POSTGRES_POOL_RECYCLE = int(os.getenv("POSTGRES_POOL_RECYCLE", 1800))

# ---- FIX: ЧИСТЫЙ DSN БЕЗ options
DATABASE_DSN = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


# ---------------------------
#     JSON LOG FORMATTER
# ---------------------------

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "trace_id": str(uuid.uuid4()),
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "source": f"{record.pathname}:{record.lineno}",
        }, ensure_ascii=False)


logging_config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": JsonFormatter}
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": APP_LOG_LEVEL.upper()
        }
    },
    "root": {
        "handlers": ["stdout"],
        "level": APP_LOG_LEVEL.upper()
    }
})

log = logging.getLogger(__name__)


# ---------------------------
#        LIFESPAN
# ---------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    # ---- FIX: передаём schema сюда
    postgres_engine = make_postgres_engine(
        dsn=DATABASE_DSN,
        schema=POSTGRES_SCHEMA
    )

    try:
        await postgres_engine.connect(
            pool_size=POSTGRES_POOL_SIZE,
            max_overflow=POSTGRES_MAX_OVERFLOW,
            pool_timeout=POSTGRES_POOL_TIMEOUT,
            pool_recycle=POSTGRES_POOL_RECYCLE
        )
        log.info("Подключение к БД успешно")

    except Exception as e:
        log.error(f"Ошибка при подключении к базе данных: {e}")
        raise RuntimeError("Не удалось подключиться к базе данных")

    # repositories + services
    calc_result_repository = make_calc_result_repository(
        postgres_engine=postgres_engine,
    )
    calc_service = CalculationService(calc_result_repository=calc_result_repository)

    # routers
    app.include_router(
        make_calc_router(
            calc_service=calc_service,
            transaction=postgres_engine.transaction
        )
    )

    yield

    # ---- disconnect
    try:
        await postgres_engine.disconnect()
        log.info("Отключение от БД успешно")
    except Exception as e:
        log.error(f"Ошибка при отключении от базы данных: {e}")


# ---------------------------
#          FASTAPI APP
# ---------------------------

app = FastAPI(lifespan=lifespan, title=APP_TITLE)


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


# ---------------------------
#        ENTRYPOINT
# ---------------------------

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_DEBUG,
        log_level=APP_LOG_LEVEL,
        workers=APP_WORKERS,
    )
