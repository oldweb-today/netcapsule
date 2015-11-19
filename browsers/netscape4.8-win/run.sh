#!/bin/bash

export WINEPREFIX="/home/browser/ns48"

PYWB_IP=$(grep netcapsule_pywb_1 /etc/hosts | cut -f 1 | head -n 1)

sed -i s/DIMENSION/$SCREEN_WIDTH"x"$SCREEN_HEIGHT/g /home/browser/ns48/user.reg

sudo chown browser:browser /home/browser/prefs.js
echo "user_pref(\"browser.window_rect\", \"0,0,$SCREEN_WIDTH,$SCREEN_HEIGHT\");" >> /home/browser/prefs.js

sed s/netcapsule_pywb_1/$PYWB_IP/g /home/browser/prefs.js > /home/browser/ns48/drive_c/Program\ Files/Netscape/Users/default/prefs.js


run_browser wine 'C:/Program Files/Netscape/Communicator/Program/netscape.exe' $URL
