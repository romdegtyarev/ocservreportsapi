#!/bin/bash


docker run --rm --network ocservnetwork --env-file .env \
  -e MODE=fetch \
  --name ocservreportsdbclient ocservreportsdbclient

