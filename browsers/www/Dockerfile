FROM netcapsule/base-browser

RUN sudo dpkg --add-architecture i386 &&\
    apt-get update && apt-get install -qqy subversion libsdl2-dev libpng-dev cmake portaudio19-dev libreadline-dev fvwm p7zip\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/browser

USER browser

RUN svn checkout svn://svn.code.sf.net/p/previous/code/trunk previous-code

RUN cd previous-code; ./configure; make;\
 touch /home/browser/previous-code/src/Previous-icon.bmp;\
 sudo make install

ADD NS33.tar.gz /home/browser/

COPY tars.iso.dmg /home/browser/

COPY previous.cfg /home/browser/.previous/previous.cfg

COPY proxy.py /home/browser/proxy.py

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

CMD /app/entry_point.sh /app/run.sh

