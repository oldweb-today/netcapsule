FROM netcapsule/base-wine-browser

WORKDIR /home/browser

COPY safari.tar.gz /home/browser/safari.tar.gz

COPY proxy.reg /home/browser/proxy.reg

RUN tar xvf /home/browser/safari.tar.gz; mv /home/browser/safari /home/browser/.safari

COPY flux-apps /home/browser/.fluxbox/apps
RUN sudo chown browser:browser -R /home/browser/.fluxbox

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

CMD /app/entry_point.sh /app/run.sh

