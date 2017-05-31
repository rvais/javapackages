#!/bin/bash
DIR=$(dirname $(readlink -f $0))

XDG_DATA_HOME="$DIR/Data/Home"
XDG_CONFIG_HOME="$DIR/Config/Home"
XDG_DATA_DIRS="$DIR/DirOne/Data:$DIR/DirTwo/Data:$DIR/DirThree/Data"
XDG_CONFIG_DIRS="$DIR/DirOne/Config:$DIR/DirTwo/Config"
XDG_CACHE_HOME="$DIR/Cache/Home"

# combine all paths so they can be created in single loop
echo -e "XDG_DATA_HOME=$XDG_DATA_HOME XDG_CONFIG_HOME=$XDG_CONFIG_HOME "
echo -e "XDG_DATA_DIRS=$XDG_DATA_DIRS XDG_CONFIG_DIRS=$XDG_CONFIG_DIRS XDG_CACHE_HOME=$XDG_CACHE_HOME" 
