FROM python:2.7
MAINTAINER Ilya Kreymer <ikreymer at gmail.com>

WORKDIR /app

ADD requirements.txt /app/

RUN pip install -r requirements.txt

ADD main.py /app/
ADD uwsgi.ini /app/
ADD . /app/

VOLUME /app/static/

CMD ["uwsgi", "uwsgi.ini"]

#CMD ["python", "main.py"]
