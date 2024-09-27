#!/bin/bash


if [ "$MODE" == "log" ]; then
    echo "Starting the logging script..."
    venv/bin/python ocservaddentry.py
elif [ "$MODE" == "fetch" ]; then
    echo "Starting the fetching script..."
    venv/bin/python ocservgetentry.py
elif [ "$MODE" == "test" ]; then
    echo "Testing database connection..."
    venv/bin/python testdb.py
else
    echo "Please set the MODE environment variable to 'log', 'fetch', or 'test'."
    exit 1
fi

