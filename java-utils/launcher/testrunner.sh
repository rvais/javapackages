#!/bin/bash
#
# "Java Launcher - Proof of Concept" test script
# Author: Roman Vais <rvais@redhat.com>
#
#==============================================================================
#
# LAUNCHER="launcher"                 # 

# definiton of variables 
APP_NAME="program"                  # name of launcher's symlink used in tests
LOG_FILE_NAME="launcher.log"        # name of log for launcher
COVERAGE_FILE_NAME="coverage.log"   # file for redirection of py covaerage stdout
PATH_TO_TESTS="./tests"             # path to dir where are test directories
PATH_TO_LOG_FILES="./logs"          # path to dir where logs are stored
ENV_FILE="env.sh"                   # script to setup XDG according to tests
SKIP_RET_CODE=3                     # min num that cannot be returbed by launcher

# options to configure behavior
RUN_COVERAGE=true     # if 'true' code coverage will be made
DEBUG_TESTED=false    # if 'true' stdout & stderr won't be redirected 

function runTest {
  local test_name="$1"
  local expected_out="${PATH_TO_TESTS%/}/${test_name%/}/expected.out" \
        expected_err="${PATH_TO_TESTS%/}/${test_name%/}/expected.err" \
        env_script="${PATH_TO_TESTS%/}/${test_name%/}/$ENV_FILE" \
        out="${PATH_TO_LOG_FILES%/}/$test_name.stdout" \
        err="${PATH_TO_LOG_FILES%/}/$test_name.stderr"

  if [ ! -f "$env_script" ]; then
    echo "# Script for setting up environmental variables missing!"
    echo "$env_script"
    return $SKIP_RET_CODE
  fi

  touch $expected_err   # if empty stderr is expected and file missing
  export $($env_script) 

  if [ ! -f "$expected_out" -o ! -f "$expected_err" ]; then
    echo "# File with expected output (stdout or stderr) missing!"
    return $SKIP_RET_CODE
  fi

  if [ "$DEBUG_TESTED" = true ]; then
    ./$APP_NAME "--jlauncher-test"
  else 
    ./$APP_NAME "--jlauncher-test" > "$out" 2> "$err"
  fi

  echo $? >> "$out"

  # if there is a log, move it
  if [ -f "./$LOG_FILE_NAME" ]; then
    mv -T "./$LOG_FILE_NAME" \
          "${PATH_TO_LOG_FILES%/}/$test_name.$LOG_FILE_NAME"
  fi

  diff "$expected_out" "$out" &> "/dev/null" && \
  diff "$expected_err" "$err" &> "/dev/null"

  return "$?"
}


#=== start script =============================================================
set -e

if [ ! -d "$PATH_TO_TESTS" ]; then
  echo "Haven't found directory with cfg files for individual test cases!" \
       "Exiting ..."
  exit 1
fi

if [ ! -d "$PATH_TO_LOG_FILES" ]; then
  mkdir -p "$PATH_TO_LOG_FILES"
fi


if [ "$RUN_COVERAGE" = true ]; then
  export COVERAGE_PROCESS_START="${PWD%/}/resources/coverage/.coveragerc"
  export PYTHONPATH="${PWD%/}/resources/coverage${PYTHONPATH:+:}${PYTHONPATH:-}"

#  printenv 
#  read -n 1

fi 

# discover test cases  
DIRECTORIES=`ls "$PATH_TO_TESTS"`

set +e

TEST_COUNT=0
for TEST_CASE in $DIRECTORIES
do
  if [ ! -d "${PATH_TO_TESTS%/}/$TEST_CASE" -o ${TEST_CASE:(-4)} != "Test" ]; then
    continue
  fi

  ((TEST_COUNT++))
done

echo "TAP version 13"
echo "1..$TEST_COUNT"

TEST_COUNT=0
for TEST_CASE in $DIRECTORIES
do

#  echo $TEST_CASE
  if [ ! -d "${PATH_TO_TESTS%/}/$TEST_CASE" -o ${TEST_CASE:(-4)} != "Test" ]; then
    continue
  fi

  ((TEST_COUNT++))
  RESULT="not ok"

  runTest "$TEST_CASE"
  STATUS="$?"

  if [ "$STATUS" == 0 ]; then
    RESULT="ok"
  fi

  echo "$RESULT $TEST_COUNT - $TEST_CASE # test return code: $STATUS"
done

# set -e
if [ "$RUN_COVERAGE" = true ]; then
  COVERAGE_LOG="${PATH_TO_LOG_FILES%/}/$COVERAGE_FILE_NAME" 
  unset PYTHONPATH COVERAGE_PROCESS_START
  coverage combine &> "$COVERAGE_LOG"
  coverage html &>> "$COVERAGE_LOG"
  coverage report &>> "$COVERAGE_LOG"
fi
# set +e

exit 0
