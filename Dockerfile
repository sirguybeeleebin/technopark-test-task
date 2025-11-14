FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --without dev

COPY app ./app

EXPOSE 8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV APP_WORKERS=1
ENV APP_LOG_LEVEL=info

CMD ["sh", "-c", "poetry run uvicorn app.main:app --host $APP_HOST --port $APP_PORT --log-level $APP_LOG_LEVEL --workers $APP_WORKERS"]
