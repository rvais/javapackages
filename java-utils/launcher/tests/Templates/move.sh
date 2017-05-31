#!/bin/bash

NAME="jlauncher.ini"

mv "XDG_CONFIG_HOME.ini" "./Config/Home/launcher/$NAME"
mv "XDG_DATA_HOME.ini" "./Data/Home/program/$NAME"
mv "XDG_CACHE_HOME.ini" "./Cache/Home/program/$NAME"

mv "XDG_DATA_DIRS.ini" "./DirOne/Data/program/$NAME"
mv "XDG_DATA_DIRS.ini" "./DirTwo/Data/program/$NAME"
mv "XDG_DATA_DIRS.ini" "./DirThree/Data/program/$NAME"

mv "XDG_CONFIG_DIRS.ini" "./DirOne/Config/launcher/$NAME"
mv "XDG_CONFIG_DIRS.ini" "./DirTwo/Config/launcher/$NAME"
