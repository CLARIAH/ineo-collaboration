FROM python:3.11-slim-buster

RUN apt update && apt install -y cron curl vim git screen iputils-ping net-tools

WORKDIR /src
COPY .env ./.env

COPY queries ./queries
COPY dsqueries ./dsqueries

COPY main.py ./main.py
COPY utils.py ./utils.py
COPY harvester.py ./harvester.py
COPY ineo_sync.py ./ineo_sync.py
COPY ineo_get_properties.py ./ineo_get_properties.py
COPY rating.py ./rating.py
COPY template.py ./template.py

COPY template_tools.json ./template_tools.json
COPY template_datasets.json ./template_datasets.json
COPY data/datasets ./data/datasets
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
#RUN crontab -l | { cat; echo "*/2 * * * * cd /src && /usr/local/bin/python /src/main.py"; } | crontab -
#ENTRYPOINT [ "cron", "-f" ]
ENTRYPOINT [ "tail","-f","/dev/null"]