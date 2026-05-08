FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data .hook_cache .tone_cache

FROM base AS production

EXPOSE 8000 8501

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
