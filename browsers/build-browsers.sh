#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

set -e

for dir in $DIR/*/
do
    dir=${dir%*/}
    name=`basename $dir`

    echo "docker build -t netcapsule/$name $dir"
    docker build -t netcapsule/$name $dir
done


