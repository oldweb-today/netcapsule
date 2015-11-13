#!/bin/bash

fluxbox -display $DISPLAY -log /tmp/fluxbox.log &

cd /download/ncsa-mosaic
./src/Mosaic $URL

