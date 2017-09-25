#!/usr/bin/env bash
BUILD_ENV=staging /usr/local/bin/docker-compose -f /srv/docker-compose.yml down; BUILD_ENV=staging /usr/local/bin/docker-compose -f /srv/docker-compose.yml up -d