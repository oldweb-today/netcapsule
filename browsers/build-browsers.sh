#!/bin/bash

set -e
docker build -t memoframe/base-browser ./generic
docker build -t memoframe/netscape ./netscape
docker build -t memoframe/firefox ./firefox

