#!/usr/bin/env bash
set -e
BASEDIR=$( cd $(dirname $0) ; pwd -P )
BUILD_ENV=staging $BASEDIR/build.sh
echo "++ finished building"