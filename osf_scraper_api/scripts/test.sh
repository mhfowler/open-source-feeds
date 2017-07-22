#!/usr/bin/env bash
BASEDIR=$( cd $(dirname $0) ; pwd -P )
echo $BASEDIR
#curl -X PUT -H "Content-Type: application/json" --data-binary "@${BASEDIR}/test.json" "http://127.0.0.1:5002/api/scrape_posts/"
curl -X PUT -H "Content-Type: application/json" --data-binary "@${BASEDIR}/test.json" "http://localhost/api/scrape_posts/"
#curl -X PUT -H "Content-Type: application/json" --data-binary "@${BASEDIR}/test.json" "http://23.20.159.171//api/scrape_posts/"