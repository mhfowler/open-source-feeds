#!/usr/bin/env bash
set -e
BASEDIR=$( cd $(dirname $0) ; pwd -P )
BUILD_ENV=staging $BASEDIR/deploy.sh
echo "++ finished deploying"