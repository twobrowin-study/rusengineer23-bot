FROM python:3.11-slim-buster

ENV DOCKER_RUN           'true'
ENV BOT_TOKEN            ''
ENV SHEETS_ACC_JSON      ''
ENV SHEETS_LINK          ''
ENV SWITCH_UPDATE_TIME   ''
ENV SETTINGS_UPDATE_TIME ''

WORKDIR /python-docker

COPY requirenments.txt .
RUN pip3 install -r requirenments.txt

COPY python/*.py ./
RUN  mkdir ./ext
COPY python/ext/*.py ./ext

CMD [ "python3", "-u", "main.py"]