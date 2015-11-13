#!/bin/bash

export WINEPREFIX="/home/browser/ie55"

wine regedit proxy.reg

sed -i s/DIMENSION/$SCREEN_WIDTH"x"$SCREEN_HEIGHT/g /home/browser/screen.reg
wine regedit /home/browser/screen.reg

wine start /max 'C:/Program Files/Internet Explorer/iexplore.exe' $URL
