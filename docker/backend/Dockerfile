# docker/backend/Dockerfile
# Handles poetry.lock issues gracefully

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

# Copy poetry.lock if it exists, regenerate if needed
COPY poetry.lock* ./

# Install dependencies with lock file regeneration if needed
RUN if [ ! -f poetry.lock ]; then \
        echo "No poetry.lock found, generating..." && \
        poetry lock --no-update; \
    fi && \
    poetry install --no-root --no-interaction --no-ansi || \
    (echo "Lock file out of sync, regenerating..." && \
     rm -f poetry.lock && \
     poetry lock --no-update && \
     poetry install --no-root --no-interaction --no-ansi)

# Ensure email-validator is installed
RUN pip install --no-cache-dir email-validator==2.2.0

# Verify installation
RUN python -c "import email_validator; print(f'email-validator {email_validator.__version__} installed successfully')"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ===== Production Stage =====
FROM base as production

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* ./

# Install dependencies with lock file handling
RUN if [ ! -f poetry.lock ]; then \
        poetry lock --no-update; \
    fi && \
    poetry install --no-root --no-interaction --no-ansi --only main || \
    (rm -f poetry.lock && \
     poetry lock --no-update && \
     poetry install --no-root --no-interaction --no-ansi --only main)

# Ensure email-validator is installed
RUN pip install --no-cache-dir email-validator==2.2.0

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs /app/uploads && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]