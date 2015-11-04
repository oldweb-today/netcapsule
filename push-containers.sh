#!/bin/bash

# Push containers to dockerhub
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# Browsers
for dir in $DIR/browsers/*/
do
    dir=${dir%*/}
    name=`basename $dir`

    echo "docker push netcapsule/$name"
    docker push netcapsule/$name
done


