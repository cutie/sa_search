FROM python:3.6.6-jessie

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY bin/watchexec /usr/bin/
RUN chmod +x /usr/bin/watchexec

RUN pip install --no-cache-dir  -r requirements.txt

ENV LC_ALL C.UTF-8