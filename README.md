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
├── app                     # Основной пакет приложения
│   ├── routers             # Слой API / маршруты FastAPI
│   │   ├── calc.py         # Реализация эндпоинтов для калькулятора
│   │   ├── calc_test.py    # Тесты для эндпоинтов калькулятора
│   │   └── __init__.py     # Делает папку Python-пакетом
│   ├── configs             # Конфигурации и настройки приложения
│   │   ├── db.py           # Настройка подключения к базе данных и менеджер сессий
│   │   ├── db_test.py      # Тесты для работы с БД и менеджера сессий
│   │   ├── __init__.py     # Делает папку Python-пакетом
│   │   └── settings.py     # Конфигурационные переменные (переменные окружения, логирвоание)
│   ├── __init__.py         # Делает app Python-пакетом
│   ├── main.py             # Точка входа приложения FastAPI (uvicorn)
│   ├── repositories        # Слой доступа к данным (DAO / Repository)
│   │   ├── calc_result.py       # Репозиторий для работы с таблицей calc_result
│   │   ├── calc_result_test.py  # Тесты репозитория calc_result
│   │   ├── __init__.py          # Делает папку Python-пакетом
│   │   └── models                # SQLAlchemy модели
│   │       ├── base.py           # Базовый класс моделей и сессия
│   │       ├── calc_result.py    # Модель таблицы calc_result
│   │       └── __init__.py       # Делает models Python-пакетом
│   └── services          # Слой бизнес-логики
│       ├── calc.py       # Сервис калькулятора (расчеты, обработка данных)
│       ├── calc_test.py  # Тесты для сервиса калькулятора
│       └── __init__.py   # Делает services Python-пакетом
├── docker-compose.yml     # Конфигурация Docker Compose (БД, сервисы)
├── Dockerfile             # Dockerfile для сборки образа приложения
├── example.env            # Пример .env файла с переменными окружения
├── Makefile               # Makefile для форматирования, тестов, запуска и очистки
├── migrations             # SQL скрипты миграций базы данных
│   └── 001_create_calc_result_table.sql  # Скрипт создания таблицы calc_result
├── poetry.lock            # Файл блокировки зависимостей Poetry
├── pyproject.toml         # Настройка Poetry, зависимости и dev-зависимости
└── README.md              # Документация проекта
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