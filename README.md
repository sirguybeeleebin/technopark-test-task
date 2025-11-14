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
├── app                          # Основной пакет приложения
│   ├── __init__.py              # Инициализация пакета app
│   ├── main.py                  # Точка входа FastAPI приложения
│   ├── repositories             # Пакет для работы с базой данных (репозитории)
│   │   ├── calc_result.py       # Репозиторий для работы с сущностью CalcResult
│   │   ├── calc_result_test.py  # Тесты для репозитория CalcResult
│   │   ├── __init__.py          # Инициализация пакета repositories
│   │   └── models               # Пакет с моделями SQLAlchemy
│   │       ├── base.py          # Базовая модель/ORM базовый класс
│   │       ├── calc_result.py   # Модель CalcResult для SQLAlchemy
│   │       └── __init__.py      # Инициализация пакета models
│   ├── routers                  # Пакет с FastAPI роутерами
│   │   ├── calc.py              # Роутеры для эндпоинтов калькулятора
│   │   ├── calc_test.py         # Тесты для роутеров калькулятора
│   │   └── __init__.py          # Инициализация пакета routers
│   ├── services                 # Пакет с бизнес-логикой / сервисами
│   │   ├── calc.py              # Сервис CalcService с бизнес-логикой
│   │   ├── calc_test.py         # Тесты для сервиса CalcService
│   │   └── __init__.py          # Инициализация пакета services
│   └── session_manager          # Пакет для работы с сессиями и транзакциями
│       ├── __init__.py          # Инициализация пакета session_manager
│       ├── session_manager.py   # Класс SessionManager и декоратор транзакций
│       └── session_manager_test.py  # Тесты для SessionManager
├── docker-compose.yml           # Конфигурация Docker Compose для приложения и БД
├── Dockerfile                   # Dockerfile для сборки контейнера приложения
├── example.env                  # Пример файла окружения с переменными
├── Makefile                     # Makefile с командами для разработки/сборки
├── migrations                   # Папка с SQL-миграциями
│   └── 001_create_calc_result_table.sql  # Скрипт создания таблицы calc_result
├── poetry.lock                  # Файл блокировки зависимостей Poetry
├── pyproject.toml               # Конфигурационный файл Poetry и проекта
└── README.md                    # Документация проекта
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