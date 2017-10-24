#!/usr/bin/env bash

# set path
export PATH=/usr/local/bin:$PATH

# cli args
pdf_path=$1

# make request
open -a Preview "${pdf_path}"