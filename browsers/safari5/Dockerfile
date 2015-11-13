FROM netcapsule/base-wine-browser

WORKDIR /home/browser

ADD safari.tar.gz /home/browser/

COPY proxy.reg /home/browser/proxy.reg

COPY flux-apps /home/browser/.fluxbox/apps
RUN sudo chown browser:browser -R /home/browser/.fluxbox

COPY screen.reg /home/browser/screen.reg

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

CMD /app/entry_point.sh /app/run.sh

