#!/usr/bin/env bash

# set path
export PATH=/usr/local/bin:$PATH

# cli args
fb_username=$1
fb_password=$2

# make request
curl -H "Content-Type: application/json" -X POST -d '{"fb_username":"'${fb_username}'","fb_password":"'${fb_password}'"}' "http://localhost:80/api/whats_on_your_mind/"