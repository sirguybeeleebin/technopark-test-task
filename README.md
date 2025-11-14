# technopark-test-task

## Описание проекта

Это REST-сервис для расчёта стоимости изделия на основе списка материалов.  
Сервис принимает JSON с материалами и их количеством/ценой, вычисляет суммарную стоимость, сохраняет результат в базу данных PostgreSQL и возвращает клиенту результат.  
Сервис написан на FastAPI с использованием SQLAlchemy и asyncpg, полностью асинхронный и готовый к запуску в Docker.

---

## Технологии

- **FastAPI** — для реализации REST API и асинхронных эндпоинтов  
- **SQLAlchemy (async)** — ORM для работы с PostgreSQL  
- **asyncpg** — асинхронный драйвер PostgreSQL  
- **Pydantic** — валидация и сериализация входных и выходных данных  
- **pytest / pytest-asyncio** — тестирование сервисного и API слоев  
- **Docker / Docker Compose** — контейнеризация приложения и базы данных

---


## Структура проекта

```
.
├── app                      # Основной пакет приложения
│   ├── api                  # REST API эндпоинты
│   │   ├── calc.py          # Эндпоинт /calc и Pydantic модели запроса/ответа
│   │   ├── calc_test.py     # Тесты для API /calc
│   │   └── __init__.py      # Пакет API
│   ├── engines              # Работа с внешними движками/соединениями
│   │   ├── __init__.py      # Пакет движков
│   │   ├── postgres.py      # Класс PostgresEngine с транзакциями и сессиями
│   │   └── postgres_test.py # Тесты для PostgresEngine
│   ├── __init__.py          # Пакет приложения
│   ├── main.py              # Точка входа FastAPI, подключение БД, роутеров, lifespan
│   ├── repositories         # Работа с базой данных (DAO)
│   │   ├── calc_result.py       # Репозиторий для сохранения результатов расчета
│   │   ├── calc_result_test.py  # Тесты для CalcResultRepository
│   │   ├── __init__.py          # Пакет репозиториев
│   │   └── models            # ORM модели SQLAlchemy
│   │       ├── base.py       # Базовый класс Base для declarative моделей
│   │       ├── calc_result.py# Модель CalcResult с схемой и колонками
│   │       └── __init__.py   # Пакет моделей
│   └── services            # Сервисный слой бизнес-логики
│       ├── calc.py          # Логика расчета стоимости и сохранения результата
│       ├── calc_test.py     # Тесты для CalculationService
│       └── __init__.py      # Пакет сервисов
├── docker-compose.yml       # Конфигурация Docker Compose для приложения и БД
├── Dockerfile               # Сборка Docker-образа приложения
├── example.env              # Пример файла с переменными окружения
├── Makefile                 # Утилиты для сборки, запуска и тестов через make
├── migrations               # SQL-миграции базы данных
│   └── 002_create_calc_result_table.sql  # Создание таблицы calc_results
├── poetry.lock              # Файл блокировки зависимостей Poetry
├── pyproject.toml           # Настройка проекта Poetry (зависимости, скрипты)
└── README.md                # Документация проекта и инструкция по запуску
```

---

## Тесты

1. корректный кейс

```
curl -X POST http://localhost:8000/calc \
  -H "Content-Type: application/json" \
  -d '{
        "materials": [
          {"name": "Сталь", "qty": 12.3, "price_rub": 54.5},
          {"name": "Алюминий", "qty": 5.5, "price_rub": 120.0}
        ]               
      }'                     
          
{"id":3,"total_cost_rub":"1330.35","created_at":"2025-11-14T06:08:53.296124Z"}%  
```

2. ошибка валидации

```
curl -X POST http://localhost:8000/calc \
  -H "Content-Type: application/json" \
  -d '{"materials":[]}'
        
{"detail":[{"type":"value_error","loc":["body","materials"],"msg":"Value error, Должен быть хотя бы один материал","input":[],"ctx":{"error":{}}}]}%                                           
```

3. ошибка сервера

```
curl -X POST http://localhost:8000/calc \
  -H "Content-Type: application/json" \
  -d '{
        "materials": [
          {"name": "Сталь", "qty": 12.3, "price_rub": 54.5},
          {"name": "Алюминий", "qty": 5.5, "price_rub": 120.0}
        ]
      }'

{"detail":"Внутренняя ошибка сервиса"}%   
```

---

## Инструкция по развертыванию

1. Создать файл `.env`, используя пример `example.env`.
2. Запустить сервис и БД через Docker Compose:

```bash
docker compose --env-file .env up --build
```