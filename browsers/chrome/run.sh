#!/bin/bash

http_proxy="http://netcapsule_pywb_1:8080" wget "http://pywb.proxy/pywb-ca.pem"

mkdir -p $HOME/.pki/nssdb
certutil -d $HOME/.pki/nssdb -N
certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "pywb" -i /home/browser/pywb-ca.pem 

mkdir ~/.config/
mkdir ~/.config/google-chrome
touch ~/.config/google-chrome/First\ Run

google-chrome --proxy-server="netcapsule_pywb_1:8080"  "$URL"
