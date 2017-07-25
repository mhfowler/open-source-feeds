#!/usr/bin/env bash
BASEDIR=$( cd $(dirname $0) ; pwd -P )
echo $BASEDIR
curl -X POST -H "Content-Type: application/json" --data-binary "@${BASEDIR}/scrape_posts.json" "http://127.0.0.1:5002/api/scrape_posts/"
#curl -X POST -H "Content-Type: application/json" --data-binary "@${BASEDIR}/scrape_friends.json" "http://127.0.0.1:5002/api/scrape_friends/"
#curl -X POST -H "Content-Type: application/json" --data-binary "@${BASEDIR}/scrape_posts.json" "http://localhost/api/scrape_posts/"
#curl -X POST -H "Content-Type: application/json" --data-binary "@${BASEDIR}/scrape_posts.json" "http://api.opensourcefeeds.com/api/scrape_posts/"
#curl -X POST -H "Content-Type: application/json" --data-binary "@${BASEDIR}/scrape_friends.json" "http://api.opensourcefeeds.com/api/scrape_friends/"