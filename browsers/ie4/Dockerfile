FROM netcapsule/base-wine-browser

USER browser
WORKDIR /home/browser

ADD ie4wine.tar.gz /home/browser/

COPY proxy.reg /home/browser/proxy.reg

COPY flux-apps /home/browser/.fluxbox/apps
RUN sudo chown browser:browser -R /home/browser/.fluxbox

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

CMD /app/entry_point.sh /app/run.sh

