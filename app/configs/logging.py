import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from logging import config as logging_config


def configure_logging(level: int = logging.INFO) -> None:
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
                    "level": level,
                    "stream": sys.stdout,
                }
            },
            "root": {
                "handlers": ["stdout"],
                "level": level,
            },
        }
    )
