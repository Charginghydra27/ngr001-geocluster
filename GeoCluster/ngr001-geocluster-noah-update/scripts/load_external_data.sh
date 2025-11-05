#!/bin/bash


LIMIT_ARG=""
if [ ! -z "$1" ]; then
    LIMIT_ARG="$1"
    echo "Loading with limit of $LIMIT_ARG records per database"
fi

docker exec -i ngr001_api python -m app.load_external_data $LIMIT_ARG
