FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OFFER_DATA_PATH=/app/data/seed/offers.example.json

WORKDIR /app

COPY apps/api/pyproject.toml /app/apps/api/pyproject.toml
COPY apps/api/src /app/apps/api/src
RUN pip install --no-cache-dir '/app/apps/api[ai]'

COPY apps/api/alembic.ini /app/apps/api/alembic.ini
COPY apps/api/migrations /app/apps/api/migrations
COPY data /app/data

EXPOSE 8000

CMD ["uvicorn", "vesta_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
