#!/bin/bash

cd /home/browser/

sudo chown browser NS33_2GB.dd

sudo chown browser ./.previous/previous.cfg
sudo chown browser proxy.py
#fluxbox -display $DISPLAY -log /tmp/fluxbox.log &
#fvwm -d $DISPLAY &

PYWB_IP=$(grep netcapsule_pywb_1 /etc/hosts | cut -f 1 | head -n 1)
sudo python proxy.py --start-url $URL --pywb-prefix http://$PYWB_IP:8080/all/ --start-ts $TS --port 80 &

run_browser Previous

