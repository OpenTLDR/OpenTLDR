#!/bin/bash

# cd to this director, for example:  cd /home/.../OpenTLDR/User_Interface

LOG=log-$(date +%Y%m%d).txt
export today=`date`
echo "Starting: $today" >> $LOG
source ~/.virtualenvs/opentldr-env/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --proxy-headers --forwarded-allow-ips='*' 2>&1 | tee -a $LOG 
