#!/bin/bash -l
#$ -e /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/ERRORS
#$ -o /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/OUTPUTS
#$ -wd /home/mfbx4mb9/work/WATER/v3
SGE_TASK_ID=1
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u 427d42b6-1b68-4647-9784-0e56f3e858fe -f log_time "START:ICHOR_MAKE_SETS.sh:$JOB_ID:$SGE_TASK_ID" "Make Sets"
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u 427d42b6-1b68-4647-9784-0e56f3e858fe -f make_sets "WATER-3000.xyz"
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u 427d42b6-1b68-4647-9784-0e56f3e858fe -f log_time "FINISH:ICHOR_MAKE_SETS.sh:$JOB_ID:$SGE_TASK_ID"
