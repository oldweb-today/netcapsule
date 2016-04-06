FROM python:3.5
MAINTAINER Ilya Kreymer <ikreymer at gmail.com>

WORKDIR /app

ADD requirements.txt /app/

RUN pip install -r requirements.txt

ADD main.py /app/
ADD uwsgi.ini /app/
ADD . /app/

VOLUME /app/static/
#VOLUME /app/browser_app.py

CMD ["uwsgi", "uwsgi.ini"]

#CMD ["python", "main.py"]
