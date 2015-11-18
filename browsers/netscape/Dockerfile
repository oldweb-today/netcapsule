FROM netcapsule/base-browser

RUN sudo dpkg --add-architecture i386
RUN apt-get update && apt-get install -y \
    libc6:i386 libncurses5:i386 libstdc++6:i386 libxpm4:i386 libxt6:i386 libxmu6:i386 fvwm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /download
USER browser

COPY install.sh /download/install.sh

RUN bash /download/install.sh

COPY preferences.js /download/preferences.js

COPY fvwm2rc /home/browser/.fvwm2rc

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

CMD /app/entry_point.sh /app/run.sh

WORKDIR /home/browser
