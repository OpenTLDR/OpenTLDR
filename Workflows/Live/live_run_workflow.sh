#!/bin/bash

LOG=log-$(date +%Y%m%d).txt
export today=`date`
echo "Starting Workflow: $today" >> $LOG

source ~/.virtualenvs/opentldr-env/bin/activate
python3 ./live_workflow.py 2>&1 | tee -a $LOG
