FROM python:3.12-slim-bookworm

STOPSIGNAL SIGKILL

RUN apt-get update && apt-get install -y \
    curl \
    git

WORKDIR /src
COPY .env ./.env

COPY queries ./queries
COPY dsqueries ./dsqueries

COPY *.py ./

COPY template_tools.json ./template_tools.json
COPY template_datasets.json ./template_datasets.json
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT [ "tail","-f","/dev/null"]