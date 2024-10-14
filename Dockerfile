FROM python:3.12

RUN apt-get update && apt-get install -y cron

WORKDIR /app
COPY requirements.txt ./

RUN set -ex; \
    pip install -U pip; \
    pip install --no-cache-dir -r requirements.txt
COPY . .

RUN echo "*/5 * * * * cd /app; /usr/local/bin/python3 manage.py rebuild_tree >> /var/log/cron.log 2>&1" > /etc/cron.d/rebuild_tree \
    && chmod 0644 /etc/cron.d/rebuild_tree \
    && touch /var/log/cron.log \
    && crontab /etc/cron.d/rebuild_tree

CMD bash -c 'cron -f & python manage.py collectstatic --noinput && python manage.py migrate && gunicorn MEDoc.wsgi:application -c gunicorn.conf.py'