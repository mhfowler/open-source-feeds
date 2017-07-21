#!/usr/bin/env bash
BASEDIR=$(dirname $(dirname $( cd $(dirname $0) ; pwd -P )))
cd $BASEDIR/devops
ansible-playbook -i hosts setup_server.yml