#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

set -e

docker build -t memoframe/base-browser $DIR/generic
docker build -t memoframe/netscape $DIR/netscape
docker build -t memoframe/firefox $DIR/firefox

