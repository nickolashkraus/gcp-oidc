FROM python:3.13-slim

WORKDIR /app

ENV POETRY_VERSION=2.2.1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true

ENV PATH="/app/.venv/bin:$PATH"

RUN pip install "poetry==${POETRY_VERSION}"

COPY poetry.lock pyproject.toml ./
RUN poetry install --only main

COPY . .
