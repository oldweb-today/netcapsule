#!/bin/bash
export GEOMETRY="$SCREEN_WIDTH""x""$SCREEN_HEIGHT""x""$SCREEN_DEPTH"

mkdir -p ~/.vnc 
x11vnc -storepasswd secret ~/.vnc/passwd

# start xvfb
Xvfb $DISPLAY -screen 0 $GEOMETRY -ac +extension RANDR &

# start websockify / novnc
bash /novnc/utils/launch.sh --vnc localhost:5900 &


http_proxy=http://netcapsule_pywb_1:8080  wget -O /tmp/res "http://set.pywb.proxy/setts?ts=$TS"


function shutdown {
  kill -s SIGTERM $NODE_PID
  wait $NODE_PID
}

# Run browser here
eval "$@" &
  
MY_IP=$(head -n 1 /etc/hosts | cut -f 1)

PYWB_IP=$(grep netcapsule_pywb_1 /etc/hosts | cut -f 1 | head -n 1)

# start controller app
python /app/app.py --my-ip "$IP" --pywb-ip "$PYWB_IP" --start-url "$URL" --start-ts "$TS" &

NODE_PID=$!

trap shutdown SIGTERM SIGINT
for i in $(seq 1 10)
do
  xdpyinfo -display $DISPLAY >/dev/null 2>&1
  if [ $? -eq 0 ]; then
    break
  fi
  echo Waiting xvfb...
  sleep 0.5
done

# start fluxbox
fluxbox -display $DISPLAY &

# start vnc
x11vnc -forever -ncache_cr -xdamage -usepw -shared -rfbport 5900 -display $DISPLAY &


wait $NODE_PID
