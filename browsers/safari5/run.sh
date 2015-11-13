#!/bin/bash

export WINEPREFIX="/home/browser/safari"

wine regedit proxy.reg

sed -i s/DIMENSION/$SCREEN_WIDTH"x"$SCREEN_HEIGHT/g /home/browser/screen.reg
wine regedit /home/browser/screen.reg

wine start /max 'C:/Program Files/Safari/Safari.exe' $URL
