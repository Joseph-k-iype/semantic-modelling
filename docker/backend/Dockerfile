# docker/backend/Dockerfile
# Multi-stage Dockerfile for backend with proper Poetry handling
# Path: docker/backend/Dockerfile

# ===== Base Stage =====
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    postgresql-client \
    libpq-dev \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.3
ENV POETRY_HOME=/opt/poetry
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 -

# ===== Development Stage =====
FROM base as development

# Copy pyproject.toml first
COPY pyproject.toml ./

# Copy poetry.lock if it exists, otherwise it will be generated
COPY poetry.lock* ./

# Install dependencies
# If poetry.lock doesn't exist or is out of sync, regenerate it
RUN if [ ! -f poetry.lock ]; then \
        echo "🔄 No poetry.lock found, generating..." && \
        poetry lock --no-update; \
    fi && \
    poetry install --no-root --no-interaction --no-ansi || \
    (echo "🔄 Lock file out of sync, regenerating..." && \
     rm -f poetry.lock && \
     poetry lock --no-update && \
     poetry install --no-root --no-interaction --no-ansi)

# Ensure critical dependencies are installed
RUN pip install --no-cache-dir \
    email-validator==2.2.0 \
    structlog==24.4.0

# Verify installation
RUN python -c "import email_validator; print(f'✅ email-validator {email_validator.__version__} installed')" && \
    python -c "import structlog; print(f'✅ structlog installed')" && \
    python -c "import fastapi; print(f'✅ FastAPI installed')" && \
    python -c "import sqlalchemy; print(f'✅ SQLAlchemy installed')"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/.cache && \
    chmod -R 755 /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ===== Production Stage =====
FROM base as production

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* ./

# Install production dependencies only
RUN if [ ! -f poetry.lock ]; then \
        poetry lock --no-update; \
    fi && \
    poetry install --no-root --no-interaction --no-ansi --only main || \
    (rm -f poetry.lock && \
     poetry lock --no-update && \
     poetry install --no-root --no-interaction --no-ansi --only main)

# Ensure critical dependencies are installed
RUN pip install --no-cache-dir \
    email-validator==2.2.0 \
    structlog==24.4.0

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs /app/uploads /app/.cache && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with multiple workers for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]