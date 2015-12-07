FROM netcapsule/base-browser

# To get a different version, use "Position Lookup" here: [https://omahaproxy.appspot.com] to find the position code for that version string,
# then look for that postition code here: [https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Linux_x64/].
# If it exists, use [https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/<POSITION_CODE>/chrome-linux.zip].
# See also [http://www.chromium.org/getting-involved/download-chromium].
RUN apt-get update && apt-get install -y libpango1.0-0 libfreetype6 libnss3-1d libnspr4-0d libasound2 libgconf-2-4 libgtk2.0-0 libnss3-tools jwm zip \
    && rm -rf /var/lib/apt/lists/* \
    && wget -q https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/72316/chrome-linux.zip \
    && unzip chrome-linux.zip -d /home/browser

# install old libgcrypt
RUN echo "deb http://ftp.de.debian.org/debian wheezy main" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y libgcrypt11

USER browser

COPY jwmrc /home/browser/.jwmrc

COPY run.sh /app/run.sh

RUN sudo chmod a+x /app/run.sh

WORKDIR /home/browser

CMD /app/entry_point.sh /app/run.sh

