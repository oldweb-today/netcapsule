FROM netcapsule/base-wine-browser

WORKDIR /home/browser

ADD safari.tar.gz /home/browser/

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

CMD /app/entry_point.sh /app/run.sh

