FROM python:2.7
MAINTAINER Ilya Kreymer <ikreymer at gmail.com>

WORKDIR /webarchive

COPY requirements.txt /webarchive/

RUN pip install -r requirements.txt

ENV PYWB_VERSION -e git+https://github.com/ikreymer/pywb.git@develop#egg=pywb-0.11.0

RUN pip install $PYWB_VERSION

COPY config.yaml /webarchive/

COPY . /webarchive/

EXPOSE 8080

CMD ["uwsgi", "/webarchive/uwsgi.ini"]
