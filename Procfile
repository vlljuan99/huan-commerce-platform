web: gunicorn config.wsgi --log-file - --workers 2
worker: celery -A config.celery worker --loglevel=info --concurrency 2
