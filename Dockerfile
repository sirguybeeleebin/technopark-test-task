FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml poetry.lock ./

# Install Python dependencies via Poetry
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

# Copy application code
COPY app ./app

EXPOSE 8000
ENV PYTHONUNBUFFERED=1
# Ensure the current directory is in PYTHONPATH
ENV PYTHONPATH=/app

# Run the app using poetry
CMD ["poetry", "run", "python", "app/main.py", "--env-file", ".env"]
