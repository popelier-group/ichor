#!/bin/bash -l
#$ -e /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/ERRORS
#$ -o /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/OUTPUTS
#$ -wd /home/mfbx4mb9/work/WATER/v3
SGE_TASK_ID=1
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u d14550a9-8fa5-4422-b25a-b0df06710f5e -f log_time "START:ICHOR_AIMALL.sh:$JOB_ID:$SGE_TASK_ID" "Submitting WFNs"
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u d14550a9-8fa5-4422-b25a-b0df06710f5e -f submit_wfns "TRAINING_SET" "['O1', 'H2', 'H3']"
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u d14550a9-8fa5-4422-b25a-b0df06710f5e -f log_time "FINISH:ICHOR_AIMALL.sh:$JOB_ID:$SGE_TASK_ID"
