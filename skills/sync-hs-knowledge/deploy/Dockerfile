FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "service.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
