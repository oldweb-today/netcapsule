#!/bin/bash

sudo chown browser:browser -R /app

mkdir /app/share

PYWB_IP=$(grep netcapsule_pywb_1 /etc/hosts | cut -f 1 | head -n 1)

run_browser BasiliskII-jit --config /app/basilisk_ii_prefs --display $DISPLAY

