#!/bin/bash
export WINEPREFIX="/home/browser/ie4"

sed -i s/DIMENSION/$SCREEN_WIDTH"x"$SCREEN_HEIGHT/g /home/browser/screen.reg
wine regedit /home/browser/screen.reg

wine regedit proxy.reg

wine start /max 'C:/Program Files/Internet Explorer/iexplore.exe' $URL

