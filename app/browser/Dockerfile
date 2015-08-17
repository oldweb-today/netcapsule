FROM selenium/standalone-firefox-debug

USER root

RUN apt-get update -y \
  && apt-get -y install \
    git \
    python2.7 \
    python-pip \
    python2.7-dev \
    python-openssl \
    libssl-dev libffi-dev \
  && easy_install --upgrade pip \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /novnc

RUN git clone https://github.com/kanaka/noVNC.git /novnc

RUN git clone https://github.com/kanaka/websockify.git /novnc/utils/websockify

#ADD run.sh /

#RUN chmod +x /run.sh

COPY entry_point.sh /opt/bin/entry_point.sh
RUN chmod +x /opt/bin/entry_point.sh

#USER seluser

EXPOSE 6080

#CMD /run.sh
