FROM debian:jessie

ENV TS 1996
ENV URL about:blank

ENV SCREEN_WIDTH 1360
ENV SCREEN_HEIGHT 1020
ENV SCREEN_DEPTH 16
ENV DISPLAY :99

RUN apt-get -y update && \
    apt-get -qqy install \
    git \
    sudo \
    python2.7 \
    python-pip \
    python2.7-dev \
    python-openssl \
    libssl-dev libffi-dev \
    net-tools \
    x11vnc \
    xvfb \
    curl \
    wget \
    vim

RUN apt-get -qqy install \
    fonts-ipafont-gothic \
    xfonts-100dpi \
    xfonts-75dpi \
    xfonts-cyrillic \
    xfonts-scalable \
    xfonts-base \
    fonts-liberation \
    fonts-arphic-bkai00mp fonts-arphic-bsmi00lp fonts-arphic-gbsn00lp fonts-arphic-gkai00mp fonts-arphic-ukai fonts-farsiweb fonts-nafees fonts-sil-abyssinica fonts-sil-ezra fonts-sil-padauk fonts-unfonts-extra fonts-unfonts-core fonts-indic fonts-thai-tlwg fonts-lklug-sinhala \
  && easy_install --upgrade pip \
  && rm -rf /var/lib/apt/lists/*

RUN sudo useradd browser --shell /bin/bash --create-home \
  && sudo usermod -a -G sudo browser \
  && echo 'ALL ALL = (ALL) NOPASSWD: ALL' >> /etc/sudoers \
  && echo 'browser:secret' | chpasswd

WORKDIR /novnc

RUN git clone https://github.com/kanaka/noVNC.git /novnc

RUN git clone https://github.com/kanaka/websockify.git /novnc/utils/websockify

WORKDIR /app/

COPY requirements.txt /app/

RUN pip install -U -r requirements.txt

COPY entry_point.sh /app/entry_point.sh

CMD /app/entry_point.sh
