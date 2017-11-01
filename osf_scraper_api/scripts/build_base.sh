#!/bin/bash -e
echo "++ building docker image for build env: ${BUILD_ENV}"
BASEDIR=$(cd $(dirname $0)/..  ; pwd -P )
BUILD_ENV=local
echo "BASEDIR: ${BASEDIR}"

if [ -n "$DOCKER_NO_CACHE" ];
    then DOCKER_ARGS=--no-cache;
fi
docker-compose -f $BASEDIR/docker-compose.$BUILD_ENV.yml build $DOCKER_ARGS osf_scraper_base
osascript -e 'display notification "finished" with title "Notification"'