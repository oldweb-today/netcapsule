FROM netcapsule/base-chromium

# To get a different version, use "Position Lookup" here: [https://omahaproxy.appspot.com] to find the position code for that version string,
# then look for that postition code here: [https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Linux_x64/].
# If it exists, use [https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/<POSITION_CODE>/chrome-linux.zip].
# See also [http://www.chromium.org/getting-involved/download-chromium].
ENV POSITION_CODE 44202

RUN wget -q https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/${POSITION_CODE}/chrome-linux.zip;\
    unzip chrome-linux.zip -d /home/browser


