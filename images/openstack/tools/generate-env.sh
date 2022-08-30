#!/bin/bash

PROJECT=$1
RELEASE=$2

echo PROJECT_REF=$(cat projects/${PROJECT}/${RELEASE}/ref)

# Check if platforms file exists
if [ -f projects/${PROJECT}/platforms ]; then
  echo PLATFORMS=$(cat projects/${PROJECT}/platforms 2>/dev/null)
else
  echo PLATFORMS=linux/amd64
fi

echo PROFILES=$(cat projects/${PROJECT}/profiles 2> /dev/null)
echo DIST_PACKAGES=$(cat projects/${PROJECT}/dist-packages 2> /dev/null)
echo PIP_PACKAGES=$(cat projects/${PROJECT}/pip-packages 2> /dev/null)
