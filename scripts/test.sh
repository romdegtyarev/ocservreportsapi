#!/bin/bash


docker run --rm --network ocservnetwork --env-file .env \
  -e MODE=test \
  --name ocservreportsdbclient ocservreportsdbclient

