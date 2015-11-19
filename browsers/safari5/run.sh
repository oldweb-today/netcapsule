#!/bin/bash

export WINEPREFIX="/home/browser/safari"

sed -i s/DIMENSION/$SCREEN_WIDTH"x"$SCREEN_HEIGHT/g /home/browser/safari/user.reg

wine regedit proxy.reg

run_browser wine start /max /W 'C:/Program Files/Safari/Safari.exe' $URL
