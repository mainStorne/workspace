FROM python:3.12 AS base

ENV PYTHONDONTWRITEBYTECODE 1  # Отключаем создание .pyc файлов
ENV PYTHONUNBUFFERED 1  # Убеждаемся, что вывод логов сразу идет в консоль (без буферизации)

ENV VENV_PATH="/opt/venv"
ENV PATH="$VENV_PATH/bin:$PATH"

WORKDIR /app

FROM ghcr.io/astral-sh/uv:0.5.21 AS uv

FROM base AS builder
ENV UV_COMPILE_BYTECODE=1

ENV UV_NO_INSTALLER_METADATA=1
ENV UV_PROJECT_ENVIRONMENT=$VENV_PATH
ENV UV_LINK_MODE=copy

RUN --mount=from=uv,source=/uv,target=/bin/uv \
  --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --no-install-project --no-editable --no-dev

FROM base AS runner
COPY --from=builder ${VENV_PATH} ${VENV_PATH}
COPY aibolit_app aibolit_app
COPY alembic.sh .
COPY alembic.ini .
COPY logging.yaml .

RUN chmod +x alembic.sh

ENTRYPOINT [ "/app/alembic.sh" ]
CMD uvicorn aibolit_app:make_app --factory --no-server-header --proxy-headers --workers 1 --port 80 --host 0.0.0.0 --log-config logging.yaml
