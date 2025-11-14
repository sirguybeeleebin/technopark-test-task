import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from logging import config as logging_config
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

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

DATABASE_DSN = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

POSTGRES_POOL_SIZE = int(os.getenv("POSTGRES_POOL_SIZE", 5))
POSTGRES_MAX_OVERFLOW = int(os.getenv("POSTGRES_MAX_OVERFLOW", 10))
POSTGRES_POOL_TIMEOUT = int(os.getenv("POSTGRES_POOL_TIMEOUT", 30))
POSTGRES_POOL_RECYCLE = int(os.getenv("POSTGRES_POOL_RECYCLE", 1800))


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "trace_id": str(uuid.uuid4()),
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
        "root": {
            "handlers": ["stdout"],
            "level": APP_LOG_LEVEL,
        },
    }
)
