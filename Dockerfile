FROM python:3.7-alpine as base
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
RUN apk add --no-cache postgresql-libs postgresql-client && \
    apk add --no-cache --virtual .build-deps gcc libffi-dev musl-dev postgresql-dev && \
    pip install awscli && \
    pip install -r requirements.txt --no-cache-dir && \
    apk --purge del .build-deps
COPY . /app/

# Bake version number
RUN apk add --no-cache --virtual .build-deps git && \
    cd /app && \
    COMMIT=`git rev-parse --short HEAD` && echo "COMMIT=\"${COMMIT}\"" > /app/creator/version_info.py && \
    VERSION=`git describe --always --tags` && echo "VERSION=\"${VERSION}\"" >> /app/creator/version_info.py && \
    cd / && \
    apk --purge del .build-deps

EXPOSE 80

CMD /app/bin/entrypoint.sh


FROM base as dev

ENV PRELOAD_DATA false
COPY dev-requirements.txt /app/
RUN apk add --no-cache --virtual .build-deps git && \
    pip install -r /app/dev-requirements.txt && \
    apk --purge del .build-deps

CMD /app/bin/dev_entrypoint.sh


FROM base as prd

RUN apk add --no-cache jq wget supervisor

RUN mkdir -p /var/log/supervisor/conf.d
COPY bin/worker.conf /etc/supervisor/conf.d/worker.conf
COPY bin/scheduler.conf /etc/supervisor/conf.d/scheduler.conf

CMD /app/bin/entrypoint.sh
