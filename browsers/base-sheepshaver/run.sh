#!/bin/bash

sudo chown browser:browser -R /app

mkdir ./share

PYWB_IP=$(grep netcapsule_pywb_1 /etc/hosts | cut -f 1 | head -n 1)

# For Netscape
sed -b -i s/netcapsule_pywb_1/$PYWB_IP/g ./NetscapePreferences

awk -v RS="\r" -v URL="$URL" '{gsub("HOME_PAGE_URL", URL, $0); print}' ./NetscapePreferences > /tmp/prefs.tmp

mv /tmp/prefs.tmp "./share/Netscape Preferences"

# For IE
echo -n "$PYWB_IP:8080" > ./share/proxy_ip
echo -n $URL > ./share/home_page


touch ./share/RUN_$RUN_BROWSER

run_browser ./SheepShaver --rom ./oldworld.rom --disk ./hd.dsk --extfs ./share/

