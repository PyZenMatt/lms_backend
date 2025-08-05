# Basic Dockerfile for Django + Gunicorn deploy
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


RUN mkdir -p /app/logs
COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate users && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn schoolplatform.wsgi:application --bind 0.0.0.0:8000"]