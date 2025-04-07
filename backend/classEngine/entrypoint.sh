#!/bin/bash

if [ "$BUILD_ENV" = "server" ]; then
    echo "Running in server mode"
    # Your special command here
    exec gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app --log-level debug
else
    echo "Running python command"
    # Your default command here
    exec python embedsearch.py
fi