FROM netcapsule/base-browser

RUN sudo dpkg --add-architecture i386 \
    && echo "deb http://httpredir.debian.org/debian jessie contrib" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y basilisk2:i386 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
USER browser

COPY performa.rom /app/
COPY basilisk_ii_prefs /app/
