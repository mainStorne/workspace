# Решение

Для решения переодичности приема был использован [cron синтаксис](https://en.wikipedia.org/wiki/Cron#CRON_expression), благодаря его гибкой настройке, легкости и большой истории.

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
    "intake_period": "0 12 ** *",
    "user_id": 0,
    "intake_finish": "2025-05-09T15:24:42.430Z",
    "intake_start": "2025-05-08T18:53:08.620660Z"
  }'
```

## Запуск

    Создайте .env файл в корне проекта

NEXT_TAKINGS_PERIOD - это конфигурационная переменная для эндпоинта next_takings, записывается в формате [ISO_8601](https://en.m.wikipedia.org/wiki/ISO_8601#Durations)

### Создание development окружения

Проект разрабатывался в среде dev containers, для создания такой же среды как и у автора, достаточно установить расширение dev containers в IDE и запустить приложение в контейнере. В этой среде будет установлена база данных *dev* и *test* на порту 5432, можно также запустить тесты в этой среде через pytest.
  
### Запуск API

```bash
docker compose up
```

### Запуск тестов

```bash
 docker compose -f docker-compose.tests.yaml up --build --exit-code-from tests
```
