#!/usr/bin/env bash

export TOPDIR=$PWD
export FC=$(which gfortran)

# Install Python Interfaces to RateFits and Other Functionality
cd $TOPDIR
python setup.py install
