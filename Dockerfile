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

RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python -c 'import django; django.setup(); print(\"DJANGO OK\")' && gunicorn core.wsgi --bind 0.0.0.0:$PORT --timeout 120 --log-level debug 2>&1 | tee /tmp/gunicorn.log"]