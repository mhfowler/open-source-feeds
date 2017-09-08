#!/usr/bin/env bash
BASEDIR=$(dirname $( cd $(dirname $0)/.. ; pwd -P ))
cd $BASEDIR/osf_dashboard
PYTHONPATH="$BASEDIR:$PYTHONPATH" alembic revision --autogenerate -m "$1"
