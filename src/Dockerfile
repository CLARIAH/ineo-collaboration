#FROM cronit/simple-cron
FROM python:3.11-slim-buster

WORKDIR /scripts
ADD FAIRdatasets_tools_harvester ./FAIRdatasets_tools_harvester
ADD requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "tail", "-f", "/dev/null" ]
