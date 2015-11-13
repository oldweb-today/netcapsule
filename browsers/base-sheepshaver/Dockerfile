FROM netcapsule/base-browser

# Install some tools required for creating the image
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libsdl1.2-dev

USER browser
WORKDIR /home/browser

#COPY ./SheepShaver /home/browser/SheepShaver

COPY oldworld.rom /home/browser/
COPY NetscapePreferences /home/browser/NetscapePreferences
COPY sheepshaver_prefs /home/browser/.sheepshaver_prefs

COPY SheepShaver /home/browser/
RUN sudo chown browser ./SheepShaver
RUN sudo chmod a+x ./SheepShaver

ADD hd.tar.gz /home/browser/
RUN sudo chown browser ./hd.dsk

ENV RUN_BROWSER netscape4.8

COPY run.sh /home/browser/run.sh
RUN sudo chown browser /home/browser/run.sh

CMD /app/entry_point.sh /home/browser/run.sh

