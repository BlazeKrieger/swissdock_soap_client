#!/bin/bash
export SWISSDOCKDTMPDIR=/tmp
python2.6 -u ~/swissdock/python/swissdock_ws/server/soaplib/swissdock_server.py --vitalit-ip=10.0.16.32 --key=/home/swissdock/.ssh/id_dsa --email swissdock.team@gmail.com --logpath=/var/log
