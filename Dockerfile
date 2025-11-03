# Production container for Flask optimization app
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 5000

# Use gunicorn with the app factory pattern
CMD gunicorn -k gthread -w 2 -b 0.0.0.0:5000 "app:create_app()"
