#!/bin/bash

name=$(basename $PWD)

docker build -t "netcapsule/$name" .
