FROM netcapsule/base-browser

RUN apt-get update && apt-get install -y libpango1.0-0 libfreetype6 libnss3-1d libnspr4-0d libasound2 libgconf-2-4 libgtk2.0-0 libnss3-tools jwm zip \
    && rm -rf /var/lib/apt/lists/*

# install old libgcrypt
RUN echo "deb http://ftp.de.debian.org/debian wheezy main" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y libgcrypt11

USER browser

WORKDIR /home/browser

COPY jwmrc /home/browser/.jwmrc

COPY run.sh /app/run.sh

RUN sudo chmod a+x /app/run.sh

CMD /app/entry_point.sh /app/run.sh

