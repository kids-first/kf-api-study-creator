FROM python:3.7 as base
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
RUN pip install awscli
COPY . /app/

EXPOSE 80

CMD /app/bin/entrypoint.sh


FROM base as dev

RUN apt-get update && apt-get install -y postgresql postgresql-contrib

ENV PRELOAD_DATA false
COPY dev-requirements.txt /app/
RUN pip install -r /app/dev-requirements.txt

CMD /app/bin/dev_entrypoint.sh


FROM base as prd

RUN apt-get update && apt-get install -y jq wget supervisor

RUN mkdir -p /var/log/supervisor/conf.d
COPY bin/worker.conf /etc/supervisor/conf.d/worker.conf

RUN wget -q -O vault.zip https://releases.hashicorp.com/vault/1.0.3/vault_1.0.3_linux_amd64.zip \ 
    && unzip vault.zip \
    && mv vault /usr/local/bin

CMD /app/bin/entrypoint.sh
