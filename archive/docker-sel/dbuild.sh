#!/usr/bin/env bash
BASEDIR=$( cd $(dirname $0) ; pwd -P )
echo "++ deleting ${BASEDIR}/day1/out/*"
rm -r $BASEDIR/day1/out/*
docker build -t docker-sel .