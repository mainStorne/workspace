# AibolitApp

Приложение для расчета расписания приема таблеток, содержит gRPC/Rest API реализацию.

## Стек Проекта

- *python*
- *uv*
- *FastAPI*
- *grpcio*
- *Docker*
- *pytest*
- *precommit*
- *PostgreSQL*
- *alembic*
- *ruff*
- *just*
- *editorconfig*

### Алгоритм составления расписания приема таблеток

Для составления расписания был использован [cron синтаксис](https://en.wikipedia.org/wiki/Cron#CRON_expression), благодаря его гибкой настройке, легкости и большой истории.

Например

**\*/5** это каждые пять единиц времени, можно создавать перечисления **5-10** и тд.

Для периодичности в один раз в день достаточно будет указать час приёма **0 12 \* \* \***

## Пример запроса

```bash
  curl -X 'POST' \
    '<http://localhost:8080/schedule>' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "medicine_name": "string",
    "intake_period": "0 12 * * *",
    "user_id": 0,
    "intake_finish": "2025-05-09T15:24:42.430Z",
    "intake_start": "2025-05-08T18:53:08.620660Z"
  }'
```

## Запуск

**Создайте .env файл в корне проекта**

```bash
POSTGRES_DB=api
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
NEXT_TAKINGS_PERIOD=P3D
SCHEDULE_LOWEST_BOUND=10:10
SCHEDULE_HIGHEST_BOUND=22:10
```

NEXT_TAKINGS_PERIOD - это конфигурационная переменная для эндпоинта next_takings, записывается в формате [ISO_8601](https://en.m.wikipedia.org/wiki/ISO_8601#Durations)

Ограничения по времени лекарств по умолчанию **с 8:00 до 22:00**, но можно настроить через переменные окружения *SCHEDULE_LOWEST_BOUND* нижняя граница и *SCHEDULE_HIGHEST_BOUND* верхняя граница соответственно, эти переменные окнужения заполяются в соответствии с [форматом времени](https://en.wikipedia.org/wiki/ISO_8601#Times).

### Создание development окружения

Проект разрабатывался в среде [Development Containers](https://containers.dev/), для создания такой же среды как и у автора, достаточно установить расширение dev containers в IDE и запустить приложение в контейнере. В этой среде будет установлена база данных *dev* и *test* на порту *5432*, установлены расширения для работы с кодом (только для vscode).
  
### Запуск API

```bash
docker compose up
```

### Запуск тестов

```bash
 docker compose -f docker-compose.tests.yaml up --build --exit-code-from tests
```
