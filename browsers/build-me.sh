#!/bin/bash

name=$(basename $PWD)

#docker build -t "netcapsule/$name" .
image_name="webrecorder/browser-$name"
docker build -t $image_name .
echo "Built $image_name"
