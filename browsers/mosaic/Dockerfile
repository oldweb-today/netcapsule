FROM netcapsule/base-browser

RUN apt-get update && apt-get install -y \
    build-essential libmotif-dev libjpeg62-turbo-dev libpng12-dev x11proto-print-dev libxmu-headers libxpm-dev libxmu-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /download

RUN git clone https://github.com/alandipert/ncsa-mosaic
RUN cd ncsa-mosaic; make linux

COPY proxy /usr/local/lib/mosaic/proxy

USER browser

COPY flux-apps /home/browser/.fluxbox/apps
RUN sudo chown browser:browser -R /home/browser/.fluxbox

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

CMD /app/entry_point.sh /app/run.sh


