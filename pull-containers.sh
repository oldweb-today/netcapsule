#!/bin/bash

# Pull all containers used by Netcapsule from Dockerhub

# Latest pywb
#docker pull ikreymer/pywb:dev


DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# Browsers
for dir in $DIR/browsers/*/
do
    dir=${dir%*/}
    name=`basename $dir`

    echo "docker pull netcapsule/$name"
    docker pull netcapsule/$name
done


