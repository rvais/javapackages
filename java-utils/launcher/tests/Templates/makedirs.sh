#!/bin/bash

XDG_DATA_HOME="./Data/Home"
XDG_CONFIG_HOME="./Config/Home"
XDG_DATA_DIRS="./DirOne/Data:./DirTwo/Data:./DirThree/Data"
XDG_CONFIG_DIRS="./DirOne/Config:./DirTwo/Config"
XDG_CACHE_HOME="./Cache/Home"

# combine all paths so they can be created in single loop
DIRS="$XDG_DATA_DIRS:$XDG_CONFIG_DIRS"
DIRS="$DIRS:$XDG_DATA_HOME:$XDG_CONFIG_HOME:$XDG_CACHE_HOME"

SEP=$IFS
IFS=":"

for D in $DIRS
do
  mkdir -v -p "${D%/}/program"
  mkdir -v -p "${D%/}/launcher"
done
IFS=$SEP

