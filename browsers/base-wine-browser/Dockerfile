FROM netcapsule/base-browser

# Adapter from suchja/wine
ENV WINE_MONO_VERSION 0.0.8
USER root

# Install some tools required for creating the image
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        unzip

# Install wine and related packages
RUN dpkg --add-architecture i386 \
        && apt-get update \
        && apt-get install -y --no-install-recommends \
                wine \
                wine32 \
        && rm -rf /var/lib/apt/lists/*

# Use the latest version of winetricks
RUN curl -SL 'http://winetricks.org/winetricks' -o /usr/local/bin/winetricks \
        && chmod +x /usr/local/bin/winetricks

# Get latest version of mono for wine
RUN mkdir -p /usr/share/wine/mono \
    && curl -SL 'http://sourceforge.net/projects/wine/files/Wine%20Mono/$WINE_MONO_VERSION/wine-mono-$WINE_MONO_VERSION.msi/download' -o /usr/share/wine/mono/wine-mono-$WINE_MONO_VERSION.msi \
    && chmod +x /usr/share/wine/mono/wine-mono-$WINE_MONO_VERSION.msi

# Wine really doesn't like to be run as root, so let's use a non-root user
USER browser
ENV HOME /home/browser
ENV WINEARCH win32

# Use xclient's home dir as working dir
WORKDIR /home/browser

COPY proxy.reg /home/browser/proxy.reg



