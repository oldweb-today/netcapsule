#!/bin/bash

export WINEPREFIX="/home/browser/safari"

wine regedit proxy.reg

wine 'C:/Program Files/Safari/Safari.exe' $URL
