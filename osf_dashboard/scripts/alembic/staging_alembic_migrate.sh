#!/usr/bin/env bash
BASEDIR=$( cd $(dirname $0)/../.. ; pwd -P )
export PYTHONPATH=$BASEDIR:$PYTHONPATH
cd $BASEDIR/osf_dashboard
PALOMA_ENV=staging alembic upgrade head
