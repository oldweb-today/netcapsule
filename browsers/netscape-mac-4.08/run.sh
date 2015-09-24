#!/bin/bash

sudo chown browser:browser -R /app

mkdir /app/share

PYWB_IP=$(grep netcapsule_pywb_1 /etc/hosts | cut -f 1 | head -n 1)

sed -b -i s/netcapsule_pywb_1/$PYWB_IP/g /app/NetscapePreferences

awk -v RS="\r" -v URL="$URL" '{gsub("HOME_PAGE_URL", URL, $0); print}' /app/NetscapePreferences > /tmp/prefs.tmp

mv /tmp/prefs.tmp "/app/share/Netscape Preferences"

BasiliskII-jit --config /app/basilisk_ii_prefs --extfs /app/share/ --display $DISPLAY

