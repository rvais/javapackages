#!/bin/bash
#
# "Java Launcher - Proof of Concept" test script
# Author: Roman Vais <rvais@redhat.com>
#
#==============================================================================
#

# definiton of variables 
CFG_FILE="jlauncher.ini" # default name of config file for launcher
TEST_ENV="$HOME/tstenv" # abs path to dir here to create test env | empty
APP_NAME="program"
LAUNCHER="launcher"

ONLY_SETUP=false
VERBOSE=false
RMLOG=true

# definition of functions

function systemCFG {

  if [ "$2" = true ]; then
      echo "$1  #$FUNCNAME"
  fi

  touch "$1"
  cat > "$1" <<- EOM
		[jvm]
		jvmBinary=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.121-1.b14.fc24.x86_64/bin/java
		options=
EOM
}

function basicCFG {

  if [ "$2" = true ]; then
      echo "$1  #$FUNCNAME"
  fi

  touch "$1"
  cat > "$1" <<- EOM
		[launcher]
		stopFurtherConfigProcessing=true
		[jvm]
		classPath=~/PersonalProjects/HelloWorld/dist/HelloWorld.jar
		mainClass=helloworld.HelloWorld
EOM
}

function appCFG {

  if [ "$2" = true ]; then
      echo "$1  #$FUNCNAME"
  fi

  touch "$1"
  cat > "$1" <<- EOM
		[launcher]
		enableAbrt=true
		stopFurtherConfigProcessing=false
		[jvm]
		classPath=~/PersonalProjects/HelloWorld/dist/HelloWorld.jar
		mainClass=helloworld.HelloWorld
		[application]
		arguments=HelloWorld! Ahoja Marvel
EOM
}

function appIncorrectCFG {

  if [ "$2" = true ]; then
      echo "$1  #$FUNCNAME"
  fi

  touch "$1"
  cat > "$1" <<- EOM
		[launcher]
		enableAbrt=false
		stopFurtherConfigProcessing=false
		[jvm]
		jvmBinary=/usr/lib/nonsence 
		classPath=~/PersonalProjects/HelloWorld/dist/HelloWorld.jar
		mainClass=helloworld.HelloWorld
		[application]
		arguments="HelloWorld! Ahoja Marvel"
EOM
}

function completeCFG {

  if [ "$2" = true ]; then
      echo "$1  #$FUNCNAME"
  fi

  touch "$1"
  cat > "$1" <<- EOM
		[launcher]
		enableAbrt=false
		stopFurtherConfigProcessing=false
		[jvm]
		jvmBinary=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.121-1.b14.fc24.x86_64/bin/java
		classPath=~/PersonalProjects/HelloWorld/dist/HelloWorld.jar
		options=-DsystemOption=vlaue
		mainClass=helloworld.HelloWorld
		[application]
		     # some kind of indented comment
		arguments=HelloWorld! "Ahoja Marvel"
		    indentedArgument
EOM
}

###=== start script ===###

if [ "$1" == "-v" -o "$2" == "-v" ] ; then
  VERBOSE=true
fi

if [ "$1" == "-r" -o "$2" == "-r" ]; then
  rm -r -v "$TEST_ENV"
fi


if [ "$RMLOG" = true ]; then
  rm "./launcher.log"
fi

# check env. variables and if empty set default
if [ -z $XDG_DATA_HOME ] ; then
  XDG_DATA_HOME="$HOME/.local/share"
fi

if [ -z $XDG_CONFIG_HOME ] ; then
  XDG_CONFIG_HOME="$HOME/.config"
fi

if [ -z $XDG_DATA_DIRS ] ; then
  XDG_DATA_DIRS="/usr/local/share:/usr/share"
fi

if [ -z $XDG_CONFIG_DIRS ] ; then
  XDG_CONFIG_DIRS="/etc/xdg"
fi

if [ -z $XDG_CACHE_HOME ] ; then
  XDG_CACHE_HOME="$HOME/.cache"
fi

# definition of 


# set test enviroment
# --------------------------------------
# This adds contets of $TEST_ENV as a prefix (unless empty string)
# to the XDG directory structure so normal user environment is
# not poluted by random luncher config files. Usefull for testing
# purposes only. Won't be in "final" proof of concept version
# 
if [ -n "$TEST_ENV" ] ; then
  XDG_DATA_HOME="$TEST_ENV${XDG_DATA_HOME%/}/"
  XDG_CONFIG_HOME="$TEST_ENV${XDG_CONFIG_HOME%/}/"
  XDG_CACHE_HOME="$TEST_ENV${XDG_CACHE_HOME%/}/"

  SEP=$IFS
  IFS=":"

  DIRS=""
  for D in $XDG_DATA_DIRS
  do
    DIRS="$DIRS:$TEST_ENV${D%/}/"
  done

  XDG_DATA_DIRS=${DIRS:1}

  DIRS=""
  for D in $XDG_CONFIG_DIRS
  do
    DIRS=":$DIRS$TEST_ENV${D%/}/"
  done

  XDG_CONFIG_DIRS=${DIRS:1}

  IFS=$SEP

#  echo "XDG_DATA_HOME: $XDG_DATA_HOME"
#  echo "XDG_CONFIG_HOME: $XDG_CONFIG_HOME"
#  echo "XDG_CACHE_HOME: $XDG_CACHE_HOME"
#  echo "XDG_DATA_DIRS: $XDG_DATA_DIRS"
#  echo "XDG_CONFIG_DIRS: $XDG_CONFIG_DIRS"

  if [ ! -d "$TEST_ENV" ] ; then

    if [ "$VERBOSE" = true ]; then
      echo "-----------------------------------------------------------------------------"
    fi

    DIRS="$DIRS:$XDG_DATA_DIRS:$XDG_CONFIG_DIRS"
    DIRS="$XDG_DATA_HOME:$XDG_CONFIG_HOME:$XDG_CACHE_HOME"

    SEP=$IFS
    IFS=":"

    for D in $DIRS
    do
      
      case "$((RANDOM % 3))" in
        "0")
          PICKED=""
        ;;
        "1")
          PICKED="$D$APP_NAME"
        ;;
        "2")
          PICKED="$D$LAUNCHER"
        ;;
      esac

      if [ -z $PICKED ]; then 
        continue
      fi

      mkdir -p "$PICKED"

      case "$((RANDOM % 8))" in 
        "2")
          systemCFG "$PICKED/$CFG_FILE" $VERBOSE
        ;;
        "0" | "3")
          basicCFG "$PICKED/$CFG_FILE" $VERBOSE
        ;;
        "4")
          appCFG "$PICKED/$CFG_FILE" $VERBOSE
        ;;
        "1" | "5")
          appIncorrectCFG "$PICKED/$CFG_FILE" $VERBOSE
        ;;
        "6")
          completeCFG "$PICKED/$CFG_FILE" $VERBOSE
        ;;
        "7")
          appIncorrectCFG "$PICKED/$CFG_FILE" $VERBOSE
        ;;
      esac

    done
    IFS=$SEP   

  else 
    if [ "$VERBOSE" = true ]; then
      echo "-----------------------------------------------------------------------------"
      find $TEST_ENV -iname jlauncher.ini
    fi
  fi
fi

# export XDG for child proceses
export -p  XDG_DATA_HOME XDG_CONFIG_HOME XDG_CACHE_HOME XDG_DATA_DIRS XDG_CONFIG_DIRS

if [ "$VERBOSE" = true ]; then
  echo "-----------------------------------------------------------------------------"
  printenv | grep "XDG_"
  echo "-----------------------------------------------------------------------------"
fi

if [ "$ONLY_SETUP" = true ]; then
    echo "Stop!"
    exit 0;
fi

echo "Running ..."

# try to run java launcher
eval "./$APP_NAME"
RETCODE="$?"
echo "-----------------------------------------------------------------------------"
echo "./$APP_NAME exited with: $RETCODE"






