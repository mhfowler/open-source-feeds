#!/usr/bin/env bash
set -e
BASEDIR=$(dirname $(dirname $( cd $(dirname $0) ; pwd -P )))
BUILD_ENV=staging $BASEDIR/bash/deploy/deploy.sh
echo "++ finished deploying"