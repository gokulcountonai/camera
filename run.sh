#!/bin/bash
sleep 30
cd  /home/edgecam/projects/knitting-rpi-gs/
python3 cam1_stream.py &
python3 start.py
