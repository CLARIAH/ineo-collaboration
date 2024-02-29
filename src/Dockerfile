FROM python:3.11-slim-buster

STOPSIGNAL SIGKILL
RUN apt update && apt install -y cron curl vim git screen iputils-ping net-tools

WORKDIR /src
COPY .env ./.env

COPY queries ./queries
COPY dsqueries ./dsqueries

COPY *.py ./

COPY template_tools.json ./template_tools.json
COPY template_datasets.json ./template_datasets.json
COPY data/datasets ./data/datasets
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
#RUN crontab -l | { cat; echo "*/2 * * * * cd /src && /usr/local/bin/python /src/main.py"; } | crontab -
#ENTRYPOINT [ "cron", "-f" ]
ENTRYPOINT [ "tail","-f","/dev/null"]