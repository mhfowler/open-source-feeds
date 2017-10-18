#!/usr/bin/env bash

# set path
export PATH=/usr/local/bin:$PATH

# make request
curl -X POST "http://localhost:80/api/restart_failed_jobs/"