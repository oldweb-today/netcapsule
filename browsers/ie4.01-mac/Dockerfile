FROM netcapsule/base-basilisk2-browser

WORKDIR /app

COPY run.sh /app/run.sh
RUN sudo chmod a+x /app/run.sh

# not actually a tar.gz, just set for git lfs support
COPY hd.tar.gz /app/hd

CMD /app/entry_point.sh /app/run.sh

