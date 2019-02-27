FROM python:3 as base
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/

EXPOSE 8080

CMD /app/bin/entrypoint.sh

FROM base as dev

ENV PRELOAD_DATA false
COPY dev-requirements.txt /app/
RUN pip install -r /app/dev-requirements.txt

CMD /app/bin/entrypoint.sh
