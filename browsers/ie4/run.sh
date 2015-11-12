#!/bin/bash

export WINEPREFIX="/home/browser/ie4"

wine regedit proxy.reg

wine 'C:/Program Files/Internet Explorer/iexplore.exe' $URL
