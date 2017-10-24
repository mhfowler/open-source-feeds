#!/usr/bin/env bash
set -e
BASEDIR=$( cd $(dirname $0) ; pwd -P )
cd $BASEDIR
BUILD_ENV=test-nov8 $BASEDIR/build.sh
echo "++ finished building"