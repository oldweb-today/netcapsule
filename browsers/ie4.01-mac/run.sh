#!/bin/bash

sudo chown browser:browser -R /app

mkdir /app/share

PYWB_IP=$(grep netcapsule_pywb_1 /etc/hosts | cut -f 1 | head -n 1)

# Proxy
echo -n -e "$PYWB_IP:8080\r" > /app/share/proxy_prefs

# URL
echo -n -e "$URL\r" >> /app/share/proxy_prefs

run_browser BasiliskII-jit --config /app/basilisk_ii_prefs --extfs /app/share/ --display $DISPLAY

