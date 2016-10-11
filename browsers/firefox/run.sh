#!/bin/bash

#fluxbox -display $DISPLAY -log /tmp/fluxbox.log &
jwm -display $DISPLAY &

sudo chown browser:browser /home/browser/ffprofile

cd /home/browser/ffprofile
sudo chown browser:browser /home/browser/ffprofile/*
chmod 644 /home/browser/ffprofile/*

#curl -x "netcapsule_pywb_1:8080" "http://pywb.proxy/proxy-ca.pem" > /tmp/proxy-ca.pem
curl -x "proxy:8080"  "http://mitm.it/cert/pem" > /tmp/proxy-ca.pem

certutil -A -n "PROXY" -t "TCu,Cuw,Tuw" -i /tmp/proxy-ca.pem -d /home/browser/ffprofile

#/opt/firefox/firefox --profile /home/browser/ffprofile -setDefaultBrowser --new-window "$URL" -width $SCREEN_WIDTH -height $SCREEN_HEIGHT
run_browser /opt/firefox/firefox --profile /home/browser/ffprofile -setDefaultBrowser --new-window "$URL"

