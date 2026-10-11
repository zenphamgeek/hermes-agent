FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
RUN pip install --no-cache-dir fastapi uvicorn typer rich pydantic pydantic-settings sqlalchemy psycopg2-binary redis celery httpx beautifulsoup4 pyyaml openpyxl python-docx PyMuPDF

COPY . /app/skills/sync-hse-knowledge/

ENV PYTHONPATH=/app/skills/sync-hse-knowledge
ENV HSE_DATABASE_URL=postgresql://hse_user:hse_pass@postgres:5432/hse_knowledge

EXPOSE 8000

CMD ["uvicorn", "service.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
