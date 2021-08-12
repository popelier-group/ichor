#!/bin/bash -l
#$ -e /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/ERRORS
#$ -o /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/OUTPUTS
#$ -wd /home/mfbx4mb9/work/WATER/v3
SGE_TASK_ID=1
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u fb3f3a5c-1e4c-4d80-896f-9257cc1d3ad2 -f log_time "START:ICHOR_FEREBUS.sh:$JOB_ID:$SGE_TASK_ID" "Making Models"
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u fb3f3a5c-1e4c-4d80-896f-9257cc1d3ad2 -f make_models "TRAINING_SET" "['O1', 'H2', 'H3']" "None" "None"
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u fb3f3a5c-1e4c-4d80-896f-9257cc1d3ad2 -f log_time "FINISH:ICHOR_FEREBUS.sh:$JOB_ID:$SGE_TASK_ID"
