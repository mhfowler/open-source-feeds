#!/usr/bin/env bash

# set path
export PATH=/usr/local/bin:$PATH

# cli args
docker_compose_file=$1

# if there is a Docker.app
# start the docker app if necessary
echo "Starting Docker.app, if necessary..."

open -g -a Docker.app

# Wait for the server to start up, if applicable.
i=0
while ! docker system info &>/dev/null; do
  (( i++ == 0 )) && printf %s 'Waiting for Docker to finish starting up...' || printf '.. waiting for docker'
  sleep 1
done
(( i )) && printf '\n'
echo "Docker is ready."

# run docker images
mkdir -p ~/Desktop/osf
docker-compose -f "${docker_compose_file}" up -d
sleep 3
