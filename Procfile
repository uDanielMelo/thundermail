web: gunicorn core.wsgi --bind 0.0.0.0:$PORT
worker: celery -A core worker --beat --loglevel=info --pool=solo
beat: celery -A core beat --loglevel=info