#!/bin/bash

# cd to correct Collector directory

LOG=./log-$(date +%Y%m%d).txt
export today=`date`
echo "Starting: $today" >> $LOG
source ~/.virtualenvs/opentldr-collectors/bin/activate

cd arxiv.org; python3 ./workflow.py  2>&1 | tee -a $LOG &
# cd bbc.org; python3 ./workflow.py  2>&1 | tee -a $LOG &
# cd npr.org; python3 ./workflow.py  2>&1 | tee -a $LOG &