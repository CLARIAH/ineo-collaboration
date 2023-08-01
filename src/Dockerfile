FROM python:3.11-slim-buster

WORKDIR /scripts
ADD FAIRdatasets_tools_harvester.py ./FAIRdatasets_tools_harvester.py
ADD requirements.txt ./
ADD regex.py ./
ADD template.py ./

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y cron curl vim git
RUN crontab -l | { cat; echo "*/10 * * * * cd /scripts && /usr/local/bin/python FAIRdatasets_tools_harvester.py"; } | crontab -
# ENTRYPOINT [ "tail", "-f", "/dev/null" ]
ENTRYPOINT [ "cron", "-f" ]