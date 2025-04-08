#!/bin/bash

# cd to correct directory

LOG=log-$(date +%Y%m%d).txt
export today=`date`
echo "Starting: $today" >> $LOG

source ~/.virtualenvs/opentldr-env/bin/activate
python3 ./collect_all.py  2>&1 | tee -a $LOG &