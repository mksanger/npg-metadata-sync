#!/bin/bash

# --login

set -eo pipefail
set -x

source /opt/conda/etc/profile.d/conda.sh

conda activate irods

export DOCKER=1

echo "Waiting for iRODS to become ready ..."
while true
do
    echo irods | iinit | grep -v USER_SOCK_CONNECT_ERR && break
    sleep 5
done
echo "iRODS is ready"

ienv
ilsresc
ils

echo "Waiting for mysql database to become ready ..."
while true
do
    mysqladmin ping -hmlwarehouse -utest -ptest -P3306 && break
    sleep 5
done

if [ ! "$*" == "/bin/bash -o pipefail"  ] && [ ! "$*" == "" ]; then
  exec "$@"
else
  pip install -e .
  PYTHONPATH="./tests:$PYTHONPATH" python -m pytest
  exec "$@"
fi

