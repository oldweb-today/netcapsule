#!/bin/bash

cd /home/browser/

#p7zip -d nxs3.3.7z 

mv ./Nextstep\ 3.3\ HD\ Image\ With\ Previous/Rev_* ./
sudo chown browser Rev_*

mv ./Nextstep\ 3.3\ HD\ Image\ With\ Previous/NS33_2GB.dd ./
sudo chown browser NS33_2GB.dd

sudo chown browser ./.previous/previous.cfg
#fluxbox -display $DISPLAY -log /tmp/fluxbox.log &
#fvwm -d $DISPLAY &

run_browser Previous

