#!/bin/bash
cd /home/flow/deeptrader
pkill -f web_api.py
sleep 2
nohup python3 src/web_api.py > logs/dashboard.log 2>&1 &
echo "Dashboard restarted, PID: $!"
echo "Check logs: tail -f logs/dashboard.log"


