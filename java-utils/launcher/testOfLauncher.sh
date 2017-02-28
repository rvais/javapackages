#!/bin/bash
#
# "Java Launcher - Proof of Concept" test script
# Author: Roman Vais <rvais@redhat.com>
#
#==============================================================================
#

# definiton of variables 
CFG_FILE="jlauncher.ini" # default name of config file for launcher
TEST_ENV="./tstenv" # abs path to dir here to create test env | empty
APP_NAME="program"
LAUNCHER="launcher"
LOG_FILE_NAME="launcher.log"
PATH_TO_CFG_FILES="./resources"
PATH_TO_LOG_FILES="./logs"

# array of specific subdirectories
declare -A SUBDIRS
SUBDIRS["XDG_CONFIG_DIRS"]="$LAUNCHER"
SUBDIRS["XDG_DATA_DIRS"]="$APP_NAME"
SUBDIRS["XDG_CONFIG_HOME"]="$LAUNCHER"
SUBDIRS["XDG_DATA_HOME"]="$APP_NAME"
SUBDIRS["XDG_CACHE_HOME"]="$APP_NAME"

# definition of test cases
function __runTest {
  eval "./$APP_NAME" > "${PATH_TO_LOG_FILES%/}/${FUNCNAME[1]}.stdout" \
                    2> "${PATH_TO_LOG_FILES%/}/${FUNCNAME[1]}.stderr" 

  echo $? >> "${PATH_TO_LOG_FILES%/}/${FUNCNAME[1]}.stdout"

  # if there is a log, move it
  if [ -f "./$LOG_FILE_NAME" ]; then
    mv -T "./$LOG_FILE_NAME" \
             "${PATH_TO_LOG_FILES%/}/${FUNCNAME[1]}.$LOG_FILE_NAME"
  fi

  diff "$1" "${PATH_TO_LOG_FILES%/}/${FUNCNAME[1]}.stdout" \
      &> "/dev/null"

  return "$?"
}

function __initTest {
  # combine all paths so they can be created in single loop
  DIRS="$XDG_DATA_DIRS:$XDG_CONFIG_DIRS"
  DIRS="$DIRS:$XDG_DATA_HOME:$XDG_CONFIG_HOME:$XDG_CACHE_HOME"

  # create test environment if it does not exixts
  if [ ! -d "$TEST_ENV" ] ; then
    SEP=$IFS
    IFS=":"

    for D in $DIRS
    do
      mkdir -p -v "${D%/}/$APP_NAME"
      mkdir -p -v "${D%/}/$LAUNCHER"
    done
    IFS=$SEP
  fi

  if [ ! -d "${PATH_TO_LOG_FILES%/}/${FUNCNAME[1]}" ]; then
    mkdir -p "${PATH_TO_LOG_FILES%/}/${FUNCNAME[1]}"
  fi

  # clean after previous tests
  SEP=$IFS
  IFS=":"

  for D in $DIRS
  do
    if [ -f "${D%/}/$APP_NAME/$CFG_FILE" ]; then
      rm "${D%/}/$APP_NAME/$CFG_FILE"
    fi
    if [ -f "${D%/}/$LAUNCHER/$CFG_FILE" ]; then
      rm "${D%/}/$LAUNCHER/$CFG_FILE"
    fi
  done
  IFS=$SEP

  # copy all config files to right places 
  FLS=`ls "${PATH_TO_CFG_FILES%/}/${FUNCNAME[1]}"`
  for FL in $FLS
  do
    if [ ${FL:0:3} != "XDG" ]; then
      continue
    fi

    # remove ".ini" suffix
    CFG_NAME=${FL::(-4)}

    # pick correct subdirectory - /application || /launcher
    # from predefined array
    SUBDIR="${SUBDIRS[$CFG_NAME]}"

    # expand directory list and pic destionation
    DEST=`cut -d":" -f1 <<< "${!CFG_NAME}"`

    # copy the file
    cp -T "${PATH_TO_CFG_FILES%/}/${FUNCNAME[1]}/$FL" \
          "$DEST/$SUBDIR/$CFG_FILE"
  done

  return 0
}

function BasicTest {
  __initTest
  __runTest "${PATH_TO_CFG_FILES%/}/$FUNCNAME/expected.out"
  return "$?"
}


###=== start script ===###

if [ ! -d "$PATH_TO_CFG_FILES" ]; then
  echo "Havent found directory with cfg files for ndividual test cases!" \
       "Exiting ..."
  exit 1
fi

# check env. variables and if empty set default
if [ -z $XDG_DATA_HOME ] ; then
  XDG_DATA_HOME="${HOME%/}/.local/share"
fi

if [ -z $XDG_CONFIG_HOME ] ; then
  XDG_CONFIG_HOME="${HOME%/}/.config"
fi

if [ -z $XDG_DATA_DIRS ] ; then
  XDG_DATA_DIRS="/usr/local/share:/usr/share"
fi

if [ -z $XDG_CONFIG_DIRS ] ; then
  XDG_CONFIG_DIRS="/etc/xdg"
fi

if [ -z $XDG_CACHE_HOME ] ; then
  XDG_CACHE_HOME="${HOME%/}/.cache"
fi

# set up test enviroment
if [ -n "$TEST_ENV" ] ; then

  # make sure that all paths do not end with slash
  XDG_DATA_HOME="${TEST_ENV%/}/${XDG_DATA_HOME#/}"
  XDG_CONFIG_HOME="${TEST_ENV%/}/${XDG_CONFIG_HOME#/}"
  XDG_CACHE_HOME="${TEST_ENV%/}/${XDG_CACHE_HOME#/}"

  SEP=$IFS
  IFS=":"

  DIRS=""
  for D in $XDG_DATA_DIRS
  do
    DIRS="$DIRS:${TEST_ENV%/}/${D#/}"
  done

  XDG_DATA_DIRS=${DIRS:1}

  DIRS=""
  for D in $XDG_CONFIG_DIRS
  do
    DIRS="$DIRS:${TEST_ENV%/}/${D#/}"
  done

  XDG_CONFIG_DIRS=${DIRS:1}

  IFS=$SEP

  echo "XDG_DATA_HOME: $XDG_DATA_HOME"
  echo "XDG_CONFIG_HOME: $XDG_CONFIG_HOME"
  echo "XDG_CACHE_HOME: $XDG_CACHE_HOME"
  echo "XDG_DATA_DIRS: $XDG_DATA_DIRS"
  echo "XDG_CONFIG_DIRS: $XDG_CONFIG_DIRS"
  echo "-------------------------------------------------------------------------------"
fi

# export XDG for tests to run in 
export XDG_DATA_HOME XDG_CONFIG_HOME XDG_CACHE_HOME XDG_DATA_DIRS XDG_CONFIG_DIRS

#run all the test cases
echo "Running following test cases:"
FUNCTIONS=`grep -e "^function [^_]" $0 | awk -F ' ' '{print $2}'`

for TEST_CASE in "$FUNCTIONS"
do
  RESULT="Failed!"
  eval "$TEST_CASE"
  if [ "$?" == 0 ]; then
    RESULT="Pass ..."
  fi

  echo "$TEST_CASE: $RESULT"
done





