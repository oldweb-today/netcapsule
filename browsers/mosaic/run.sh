#!/bin/bash

#fluxbox -display $DISPLAY -log /tmp/fluxbox.log &
fvwm -d $DISPLAY &

cd /download/ncsa-mosaic
./src/Mosaic $URL

