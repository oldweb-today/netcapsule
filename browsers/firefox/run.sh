#!/bin/bash

fluxbox -display $DISPLAY -log /tmp/fluxbox.log &

sudo chown browser:browser /home/browser/ffprofile

cd /home/browser/ffprofile
sudo chown browser:browser /home/browser/ffprofile/*
chmod 644 /home/browser/ffprofile/*

curl -x "netcapsule_pywb_1:8080" "http://pywb.proxy/pywb-ca.pem" > /tmp/pywb-ca.pem

certutil -A -n "PYWB" -t "TCu,Cuw,Tuw" -i /tmp/pywb-ca.pem -d /home/browser/ffprofile

/opt/firefox/firefox --profile /home/browser/ffprofile -setDefaultBrowser --new-window "$URL" -width $SCREEN_WIDTH -height $SCREEN_HEIGHT
