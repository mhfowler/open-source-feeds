#!/usr/bin/env bash
set -e
BASEDIR=$(dirname $( cd $(dirname $0) ; pwd -P ))
cd $BASEDIR

# build the docker image
$BASEDIR/scripts/build.sh

# deploy to docker hub
docker tag "${BUILD_ENV}_osf_dashboard" "mfowler/${BUILD_ENV}_osf_dashboard"
docker push "mfowler/${BUILD_ENV}_osf_dashboard"

# use ansible to deploy the docker image in the cloud
cd $BASEDIR/devops
ansible-playbook -i hosts "${BUILD_ENV}_deploy.yml"