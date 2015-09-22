FROM netcapsule/base-wine-browser

USER browser
WORKDIR /home/browser

COPY ie55wine.tar.gz /home/browser/ie55wine.tar.gz

COPY proxy.reg /home/browser/proxy.reg

RUN tar xvf /home/browser/ie55wine.tar.gz; mv /home/browser/ie55 /home/browser/.ie55

COPY flux-apps /home/browser/.fluxbox/apps
RUN sudo chown browser:browser -R /home/browser/.fluxbox

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

CMD /app/entry_point.sh /app/run.sh

