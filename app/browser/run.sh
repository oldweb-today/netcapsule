#!/bin/bash

#ip=$(head -n 1 /etc/hosts | cut -f 1)
#redis-cli -h redis_1 lpush $NODE_KEY $ip

bash /novnc/utils/launch.sh --vnc localhost:5900 &

bash /opt/bin/entry_point.sh
