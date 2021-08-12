#!/bin/bash -l
#$ -e /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/ERRORS
#$ -o /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/OUTPUTS
#$ -wd /home/mfbx4mb9/work/WATER/v3
SGE_TASK_ID=1
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u e266b1a5-16ee-4ab8-928c-3ec4edd83626 -f log_time "START:ICHOR_ADAPTIVE_SAMPLING.sh:$JOB_ID:$SGE_TASK_ID" "Adaptive Sampling"
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u e266b1a5-16ee-4ab8-928c-3ec4edd83626 -f adaptive_sampling "FEREBUS/MODELS" "SAMPLE_POOL"
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u e266b1a5-16ee-4ab8-928c-3ec4edd83626 -f log_time "FINISH:ICHOR_ADAPTIVE_SAMPLING.sh:$JOB_ID:$SGE_TASK_ID"
