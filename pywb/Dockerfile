FROM ikreymer/pywb:dev
MAINTAINER Ilya Kreymer <ikreymer at gmail.com>

RUN pip install git+https://github.com/ikreymer/py-memento-client.git@no-uri-checks

CMD ["uwsgi", "/webarchive/uwsgi.ini"]
