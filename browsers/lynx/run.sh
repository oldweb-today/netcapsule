#!/bin/bash

#fvwm -d $DISPLAY &

sudo chmod a+x /usr/bin/xterm

run_browser xterm -maximized -w 0 -bd black -fg white -bg black -e 'lynx -use_mouse -telnet -restrictions=shell,file_url "$URL"'

