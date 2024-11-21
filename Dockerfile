
FROM python:3.12-slim


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.0 \
    PYTHONPATH=/app


RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /var/lib/apt/lists/*


ENV PATH="/root/.local/bin:$PATH"


WORKDIR /app


COPY pyproject.toml poetry.lock /app/


RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi


COPY . /app/


EXPOSE 8000


CMD ["python", "-m", "main"]

