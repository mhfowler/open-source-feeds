#!/bin/bash -e
echo "++ building docker image for build env: ${BUILD_ENV}"
BASEDIR=$(cd $(dirname $0)/..  ; pwd -P )
echo "BASEDIR: ${BASEDIR}"
echo "++ compiling nunjucks templates"
nunjucks *.njk -p $BASEDIR/devops/templates \
    -o $BASEDIR/devops/build \
    -e "$BASEDIR/devops/config/${BUILD_ENV}.json"
echo "++ building docker image"

if [ -n "$DOCKER_NO_CACHE" ];
    then DOCKER_ARGS=--no-cache;
fi
docker-compose -f $BASEDIR/docker-compose.${BUILD_ENV}.yml build $DOCKER_ARGS osf_scraper_api
osascript -e 'display notification "finished" with title "Notification"'