#!/usr/bin/env bash

# set path
export PATH=/usr/local/bin:$PATH

# if docker is not installed, then exit
if ! (open -Ra "Docker.app" || which docker) ; then
  exit 7
fi