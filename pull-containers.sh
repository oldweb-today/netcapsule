#!/bin/bash

# Pull all containers used by Netcapsule from Dockerhub

# Latest pywb
docker pull ikreymer/pywb:dev

# Netcapsule
docker pull netcapsule/base-browser
docker pull netcapsule/netscape
docker pull netcapsule/firefox
docker pull netcapsule/mosaic

docker pull netcapsule/base-wine-browser
docker pull netcapsule/ie4
docker pull netcapsule/ie55
