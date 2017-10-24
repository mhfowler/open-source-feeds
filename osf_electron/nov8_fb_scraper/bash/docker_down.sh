#!/usr/bin/env bash

# set path
export PATH=/usr/local/bin:$PATH

# cli args
docker_compose_file=$1

# run docker-compose down
osascript -e 'quit app "Docker"'
docker-compose -f $docker_compose_file down
