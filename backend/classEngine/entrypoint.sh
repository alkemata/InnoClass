#!/bin/bash

exec gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app:app --log-level debug
