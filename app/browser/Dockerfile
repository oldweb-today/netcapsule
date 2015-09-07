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
    net-tools \
    xfonts-base fonts-arphic-bkai00mp fonts-arphic-bsmi00lp fonts-arphic-gbsn00lp fonts-arphic-gkai00mp fonts-arphic-ukai fonts-farsiweb fonts-nafees fonts-sil-abyssinica fonts-sil-ezra fonts-sil-padauk fonts-unfonts-extra fonts-unfonts-core ttf-indic-fonts fonts-thai-tlwg fonts-lklug-sinhala \
  && easy_install --upgrade pip \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /novnc

RUN git clone https://github.com/kanaka/noVNC.git /novnc

RUN git clone https://github.com/kanaka/websockify.git /novnc/utils/websockify

WORKDIR /opt/bin/

ADD requirements.txt /opt/bin/

RUN pip install -U -r requirements.txt

ENV URL ''
ENV TS ''

COPY app.py /opt/bin/app.py
COPY entry_point.sh /opt/bin/entry_point.sh
RUN chmod +x /opt/bin/entry_point.sh

EXPOSE 6080
EXPOSE 6082
