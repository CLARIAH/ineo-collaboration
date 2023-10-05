FROM python:3.11-slim-buster

RUN apt update && apt install -y cron curl vim git

WORKDIR /src
ADD main.py ./main.py
ADD harvester.py ./harvester.py
ADD template.py ./template.py
ADD template.json ./template.json
ADD ineo_sync.py ./ineo_sync.py
ADD .env ./.env

ADD requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
RUN crontab -l | { cat; echo "*/2 * * * * cd /src && /usr/local/bin/python /src/main.py"; } | crontab -
#ENTRYPOINT [ "cron", "-f" ]
ENTRYPOINT [ "tail","-f","/dev/null"]