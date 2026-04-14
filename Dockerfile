FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && echo 'MIGRATE OK' && python manage.py collectstatic --noinput && echo 'STATIC OK' && gunicorn core.wsgi --bind 0.0.0.0:$PORT --timeout 120 && echo 'GUNICORN OK'"]