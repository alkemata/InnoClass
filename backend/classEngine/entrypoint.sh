#!/bin/bash

exec gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app --log-level debug
