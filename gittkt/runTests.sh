#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON2=$(which python2)
PYTHON3=$(which python3)
PYTHON4=$(which python4)

if [ -n "$PYTHON2" ]; then
    #make sure we have a python2 environment
    ls -d $SCRIPT_DIR/../virtualenv/py2.* > /dev/null 2>&1
    if [ $? != 0 ]; then
        bash ../virtualenv/SetupPythonEnvironment.sh "$PYTHON2" || exit $?
    fi
    PYTHON2_ENV=$(ls -d $SCRIPT_DIR/../virtualenv/py2.*)
fi

if [ -n "$PYTHON3" ]; then
    #make sure we have a python3 environment
    ls -d $SCRIPT_DIR/../virtualenv/py3.* > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        bash ../virtualenv/SetupPythonEnvironment.sh "$PYTHON3" || exit $?
    fi
    PYTHON3_ENV=$(ls -d $SCRIPT_DIR/../virtualenv/py3.*)
fi

OS=$(uname -s)
if [ ! -z $(echo $OS | grep -i "mingw") ]; then
    INTERMEDIATE_DIR=Scripts
else
    INTERMEDIATE_DIR=bin
fi

if [ -n "$PYTHON2_ENV" ]; then
    echo ======================================
    echo Python 2
    echo --------------------------------------
    . "$PYTHON2_ENV/$INTERMEDIATE_DIR/activate"
    python --version
    python tests/t_all_tests.py $@
    echo ======================================
fi

if [ -n "$PYTHON3_ENV" ]; then
    echo ======================================
    echo Python 3
    echo --------------------------------------
    . "$PYTHON3_ENV/$INTERMEDIATE_DIR/activate"
    python --version
    coverage --version
    coverage run tests/t_all_tests.py $@
    echo ======================================
fi

if [ -z $1 ]; then
    coverage report -m --omit=tests/*
fi
