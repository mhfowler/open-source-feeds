#!/usr/bin/env bash
set -e
BASEDIR=$(dirname $(dirname $( cd $(dirname $0) ; pwd -P )))
cd $BASEDIR

# build the docker image
$BASEDIR/bash/deploy/build.sh $BUILD_ENV

# deploy to docker hub
docker tag $BUILD_ENV_osf_scraper_api "mfowler/$BUILD_ENV_osf_scraper_api "
docker push "mfowler/$BUILD_ENV_osf_scraper_api"

# use ansible to deploy the docker image in the cloud
cd $BASEDIR/devops
ansible-playbook -i hosts ${BUILD_ENV}_deploy.yml