#!/bin/bash
export GEOMETRY="$SCREEN_WIDTH""x""$SCREEN_HEIGHT""x""$SCREEN_DEPTH"

mkdir -p ~/.vnc 
x11vnc -storepasswd secret ~/.vnc/passwd

echo "LAUNCH NOVNC"
bash /novnc/utils/launch.sh --vnc localhost:5900 &
echo "END LAUNCH NOVNC"

NETSCAPE=/home/netscape/.netscape

sudo chown netscape:netscape $NETSCAPE
chmod 700 $NETSCAPE

cd $NETSCAPE

sudo chown netscape:netscape ./preferences.js
chmod 644 ./preferences.js

mkdir ./archive
mkdir ./cache

chmod 700 ./archive
chmod 700 ./cache

PYWB_IP=$(grep memoframe_pywb_1 /etc/hosts | cut -f 1 | head -n 1)

sed -i s/memoframe_pywb_1/$PYWB_IP/g ./preferences.js

awk -v URL="$URL" '{gsub("HOME_PAGE_URL", URL, $0); print}' ./preferences.js > /tmp/prefs.tmp && mv /tmp/prefs.tmp  ./preferences.js

export http_proxy=http://memoframe_pywb_1:8080
wget -o /tmp/res "http://set.pywb.proxy/setts?ts=$TS"

cd /opt/netscape

export XKEYSYMDB=XKeysymDB
export LD_LIBRARY_PATH=/opt/netscape/lib

function shutdown {
  kill -s SIGTERM $NODE_PID
  wait $NODE_PID
}


#xvfb-run --server-args="$DISPLAY -screen 0 $GEOMETRY -ac +extension RANDR" \

Xvfb $DISPLAY -screen 0 $GEOMETRY -ac +extension RANDR &

/opt/netscape/lib/ld-linux.so.2 /opt/netscape/netscape -no-about-splash &
  
IP=$(head -n 1 /etc/hosts | cut -f 1)

echo "$IP"
echo "$URL"
echo "$TS"

python /opt/bin/app.py "$IP" "$URL" "$TS" &

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

fluxbox -display $DISPLAY &

x11vnc -forever -usepw -shared -rfbport 5900 -display $DISPLAY &

wait $NODE_PID
