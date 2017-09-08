#!/usr/bin/env bash
BASEDIR=$(dirname $( cd $(dirname $0)/../; pwd -P ))
export PYTHONPATH=$BASEDIR:$PYTHONPATH
cd $BASEDIR/osf_dashboard
PALOMA_ENV=local alembic upgrade head
