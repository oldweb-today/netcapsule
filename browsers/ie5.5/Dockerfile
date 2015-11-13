FROM netcapsule/base-wine-browser

USER browser
WORKDIR /home/browser

ADD ie55wine.tar.gz /home/browser/

COPY proxy.reg /home/browser/proxy.reg

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

CMD /app/entry_point.sh /app/run.sh

