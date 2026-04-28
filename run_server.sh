#!/bin/bash
cd /home/momen/MLBB-AI-Draft-Assistant/mlbb-draft-assistant
nohup python3 -m uvicorn api_server.main:app --host 0.0.0.0 --port 8080 > /tmp/uvicorn.log 2>&1 &
echo $! > /tmp/uvicorn.pid
echo "Server started with PID: $(cat /tmp/uvicorn.pid)"
