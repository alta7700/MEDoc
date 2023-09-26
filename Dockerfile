FROM python:3.10.7-slim-bullseye

WORKDIR /app
COPY requirements.txt ./
RUN set -ex; \
    pip install -U pip; \
    pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT /app/docker-entrypoint.sh