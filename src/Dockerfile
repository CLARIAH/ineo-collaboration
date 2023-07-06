#FROM cronit/simple-cron
FROM python:3.11-slim-buster

WORKDIR /scripts
ADD FAIRdatasets_tools_harvester.py ./FAIRdatasets_tools_harvester.py
ADD requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y cron curl vim

ENTRYPOINT [ "tail", "-f", "/dev/null" ]
