# Use a lightweight Python image as the base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.0 \
    PYTHONPATH=/app

# Install system dependencies required for building the project and for Poetry
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /var/lib/apt/lists/*

# Add Poetry's bin directory to the PATH
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory in the container to match your project directory
WORKDIR /app

# Copy only the poetry files to leverage Docker cache
COPY pyproject.toml poetry.lock /app/

# Install project dependencies using Poetry, without virtual environments
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy the entire project into the container
COPY . /app/

# Expose the port your FastAPI app runs on
EXPOSE 8000

# Set the command to run the application using uvicorn
CMD ["python", "-m", "main"]

# Health check to ensure the FastAPI app is up and running
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/healthcheck || exit 1
