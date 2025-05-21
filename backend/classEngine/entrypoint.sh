#!/bin/bash

exec gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 api-server:app --log-level debug
