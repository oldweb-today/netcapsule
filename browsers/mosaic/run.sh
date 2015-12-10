#!/bin/bash

unset http_proxy
unset https_proxy
#fluxbox -display $DISPLAY -log /tmp/fluxbox.log &
fvwm -d $DISPLAY &

cd /download/ncsa-mosaic
run_browser ./src/Mosaic $URL

