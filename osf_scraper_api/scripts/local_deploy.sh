#!/usr/bin/env bash
set -e
BASEDIR=$( cd $(dirname $0) ; pwd -P )
cd $BASEDIR
BUILD_ENV=local $BASEDIR/build.sh
echo "++ finished building"

# deploy to docker hub
docker push "mfowler/local_osf_scraper_api"