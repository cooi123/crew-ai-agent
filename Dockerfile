FROM python:3.11 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN python -m venv .venv

COPY pyproject.toml .
COPY src/ ./src/
COPY app.py .

# Install using editable mode to support src layout
RUN .venv/bin/pip install --upgrade pip
RUN .venv/bin/pip install -e .

FROM python:3.11
WORKDIR /app

COPY --from=builder /app/.venv .venv/
COPY . .

# Ensure the Flask app can find packages under src/
ENV PYTHONPATH=/app/src

CMD ["/app/.venv/bin/flask", "run", "--host=0.0.0.0", "--port=8000"]