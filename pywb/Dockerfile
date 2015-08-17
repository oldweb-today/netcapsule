FROM python:2.7
MAINTAINER Ilya Kreymer <ikreymer at gmail.com>

WORKDIR /webarchive

COPY requirements.txt /webarchive/

RUN pip install -U -r requirements.txt

COPY config.yaml /webarchive/

COPY . /webarchive/

EXPOSE 8080

CMD ["uwsgi", "/webarchive/uwsgi.ini"]
