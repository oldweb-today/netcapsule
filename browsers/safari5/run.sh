#!/bin/bash

export WINEPREFIX="/home/browser/safari"

sed -i s/DIMENSION/$SCREEN_WIDTH"x"$SCREEN_HEIGHT/g /home/browser/safari/user.reg

wine regedit proxy.reg

wine start /max 'C:/Program Files/Safari/Safari.exe' $URL
