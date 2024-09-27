#!/bin/bash


if [ "$1" == "test" ]; then
  USERNAME="test_user_$(shuf -i 1000-9999 -n 1)"
  REASON=$(shuf -e "connect" "disconnect" -n 1)
  IP_REAL="192.168.1.$(shuf -i 1-254 -n 1)"
  IP_REMOTE="192.168.1.$(shuf -i 1-254 -n 1)"
  STATS_BYTES_IN=$(shuf -i 1000-1000000 -n 1)
  STATS_BYTES_OUT=$(shuf -i 1000-1000000 -n 1)
  STATS_DURATION=$(shuf -i 1-3600 -n 1)
fi

WORK_DIR=
PROJECT_DIR=
DIRECTORY=

docker run --rm --network ocservnetwork --env-file ${PROJECT_DIR}/.env -v ${WORK_DIR}:${DIRECTORY} \
  -e MODE=log \
  -e USERNAME=$USERNAME \
  -e REASON=$REASON \
  -e IP_REAL=$IP_REAL \
  -e IP_REMOTE=$IP_REMOTE \
  -e STATS_BYTES_IN=$STATS_BYTES_IN \
  -e STATS_BYTES_OUT=$STATS_BYTES_OUT \
  -e STATS_DURATION=$STATS_DURATION \
  --name ocservreportsdbclient ocservreportsdbclient

