#!/usr/bin/env bash

# set path
export PATH=/usr/local/bin:$PATH

# cli args
redis_path=$1

# make request
rm -rf $redis_path
curl -X POST "http://localhost:80/api/stop/"