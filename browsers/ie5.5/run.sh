#!/bin/bash

export WINEPREFIX="/home/browser/ie55"

wine regedit proxy.reg

wine 'C:/Program Files/Internet Explorer/iexplore.exe' $URL
