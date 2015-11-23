#!/bin/bash

sudo chown -R browser /home/browser/safari3

export WINEPREFIX="/home/browser/safari3"

sed -i s/DIMENSION/$SCREEN_WIDTH"x"$SCREEN_HEIGHT/g /home/browser/safari3/user.reg

wine regedit proxy.reg

run_browser wine start /max /W 'C:/Program Files/Safari/Safari.exe' $URL
