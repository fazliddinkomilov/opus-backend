FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Shell form so $PORT (Railway/PaaS) is honoured; falls back to 8000 locally.
CMD sh -c "uvicorn config.asgi:application --host 0.0.0.0 --port ${PORT:-8000}"
