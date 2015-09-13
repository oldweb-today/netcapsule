FROM ubuntu:trusty

RUN sudo dpkg --add-architecture i386
RUN apt-get update && apt-get install -y wget libc6:i386 libncurses5:i386 libstdc++6:i386 libxpm4:i386 libxt6:i386 libxmu6:i386\
    x11vnc xvfb fluxbox

WORKDIR /download

RUN wget http://ftp.netscape.com/pub/communicator/english/4.79/unix/supported/linux22/navigator_standalone/navigator-v479-us.x86-unknown-linux2.2.tar.gz;
RUN tar xvfz navigator-v479-us.x86-unknown-linux2.2.tar.gz

RUN cd /download/navigator-v479.x86-unknown-linux2.2; ./ns-install; echo 0;

WORKDIR /download

RUN wget http://archive.debian.org/debian/pool/main/e/egcs1.1/libstdc++2.9-glibc2.1_2.91.66-4_i386.deb
RUN wget http://archive.debian.org/debian/pool/main/g/glibc/libc6_2.2.5-11.8_i386.deb
RUN wget http://archive.debian.org/debian/pool/main/x/xfree86/xlibs_4.1.0-16woody6_i386.deb

RUN mkdir /tmp/oldlibs

RUN dpkg -x /download/libstdc++2.9-glibc2.1_2.91.66-4_i386.deb /tmp/oldlibs; \
    dpkg -x /download/libc6_2.2.5-11.8_i386.deb /tmp/oldlibs; \
    dpkg -x /download/xlibs_4.1.0-16woody6_i386.deb /tmp/oldlibs

RUN mkdir /opt/netscape/lib
RUN cp /tmp/oldlibs/usr/X11R6/lib/*.so.* /opt/netscape/lib; \
    cp /tmp/oldlibs/usr/lib/*.so.* /opt/netscape/lib; \
    cp /tmp/oldlibs/lib/*.so.* /opt/netscape/lib


RUN sudo mkdir -p /usr/X11R6/lib/X11
RUN sudo ln -s /usr/share/X11/locale /usr/X11R6/lib/X11/

RUN apt-get -qqy --no-install-recommends install \
    fonts-ipafont-gothic \
    xfonts-100dpi \
    xfonts-75dpi \
    xfonts-cyrillic \
    xfonts-scalable \
    xfonts-base
#    fonts-arphic-bkai00mp \
#    fonts-arphic-bsmi00lp \
#    fonts-arphic-gbsn00lp \
#    fonts-arphic-gkai00mp \
#    fonts-arphic-ukai \
#    fonts-farsiweb \
#    fonts-nafees \
#    fonts-sil-abyssinica \
#    fonts-sil-ezra \
#    fonts-sil-padauk \
#    fonts-unfonts-extra \
#    fonts-unfonts-core \
#    ttf-indic-fonts \
#    fonts-thai-tlwg \
#    fonts-lklug-sinhala

RUN apt-get -y install \
    git \
    python2.7 \
    python-pip \
    python2.7-dev \
    python-openssl \
    libssl-dev libffi-dev \
    net-tools

WORKDIR /novnc

RUN git clone https://github.com/kanaka/noVNC.git /novnc

RUN git clone https://github.com/kanaka/websockify.git /novnc/utils/websockify

WORKDIR /opt/bin/

ADD requirements.txt /opt/bin/

RUN pip install -U -r requirements.txt

COPY vnc_auto.html /novnc/vnc_auto.html

COPY app.py /opt/bin/app.py

ADD entry_point.sh /entry_point.sh
RUN chmod a+x /entry_point.sh

RUN sudo useradd netscape --shell /bin/bash --create-home \
  && sudo usermod -a -G sudo netscape \
  && echo 'ALL ALL = (ALL) NOPASSWD: ALL' >> /etc/sudoers \
  && echo 'netscape:secret' | chpasswd

USER netscape

RUN mkdir /home/netscape/.netscape/

COPY preferences.js /home/netscape/.netscape/preferences.js

WORKDIR /opt/netscape

ENV TS 1996
ENV URL about:blank

ENV SCREEN_WIDTH 1360
ENV SCREEN_HEIGHT 1020
ENV SCREEN_DEPTH 24
ENV DISPLAY :99

CMD /entry_point.sh
