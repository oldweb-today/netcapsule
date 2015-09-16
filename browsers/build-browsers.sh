#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

set -e

docker build -t netcapsule/base-browser $DIR/base-browser
docker build -t netcapsule/netscape $DIR/netscape
docker build -t netcapsule/firefox $DIR/firefox
docker build -t netcapsule/mosaic $DIR/mosaic

