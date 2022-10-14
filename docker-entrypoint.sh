python manage.py collectstatic --noinput
gunicorn MEDoc.wsgi:application -c gunicorn.conf.py