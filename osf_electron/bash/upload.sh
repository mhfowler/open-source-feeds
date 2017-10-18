#!/usr/bin/env bash

# set path
export PATH=/usr/local/bin:$PATH

# cli args
fb_username=$1

# make request
curl -H "Content-Type: application/json" -X POST -d '{"fb_username":"'${fb_username}'"}' "http://localhost:80/api/upload/"