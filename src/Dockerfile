FROM python:3.11-slim-buster

RUN apt update && apt install -y cron curl vim git

WORKDIR /src
COPY main.py ./main.py
COPY harvester.py ./harvester.py
COPY template.py ./template.py
COPY template.json ./template.json
COPY ineo_sync.py ./ineo_sync.py
COPY queries ./queries
COPY vocabs ./vocabs
COPY .env ./.env
COPY rating.py ./rating.py

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
#RUN crontab -l | { cat; echo "*/2 * * * * cd /src && /usr/local/bin/python /src/main.py"; } | crontab -
#ENTRYPOINT [ "cron", "-f" ]
ENTRYPOINT [ "tail","-f","/dev/null"]