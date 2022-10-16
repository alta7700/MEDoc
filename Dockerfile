FROM python:3.10.7-slim-bullseye

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN set -ex; \
    pip install -U pip; \
    pip install --no-cache-dir -r requirements.txt
COPY . .
CMD bash -c 'python manage.py collectstatic --noinput && gunicorn MEDoc.wsgi:application -c gunicorn.conf.py'