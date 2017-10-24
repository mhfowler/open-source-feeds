#!/usr/bin/env bash

# set path
export PATH=/usr/local/bin:$PATH

# cli args
log_file=$1

# tail log
touch $log_file
echo " " >> $log_file
tail -f $log_file
