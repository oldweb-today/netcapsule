FROM netcapsule/base-browser

RUN apt-get update && apt-get install -y \
    build-essential libmotif-dev libjpeg62-turbo-dev libpng12-dev x11proto-print-dev libxmu-headers libxpm-dev libxmu-dev fvwm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /download

RUN git clone https://github.com/alandipert/ncsa-mosaic
RUN cd ncsa-mosaic; make linux

COPY proxy /usr/local/lib/mosaic/proxy

USER browser

COPY fvwm2rc /home/browser/.fvwm2rc

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

WORKDIR /home/browser

CMD /app/entry_point.sh /app/run.sh


