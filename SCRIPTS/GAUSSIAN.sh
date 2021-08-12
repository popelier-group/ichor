#!/bin/bash -l
#$ -wd /home/mfbx4mb9/work/WATER/v3
# $ -pe smp 2
#$ -o /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/OUTPUTS
#$ -e /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/ERRORS
SGE_TASK_ID=1
export OMP_NUM_THREADS=2
export OMP_PROC_BIND=true
module load apps/gaussian/g09
ICHOR_DATFILE=/home/mfbx4mb9/work/WATER/v3/.DATA/JOBS/DATAFILES/427d42b6-1b68-4647-9784-0e56f3e858fe
arr1=()
arr2=()
while IFS=, read -r var1 var2
do
    arr1+=($var1)
    arr2+=($var2)
done < $ICHOR_DATFILE

ICHOR_N_TRIES=0
export ICHOR_TASK_COMPLETED=false
while [ "$ICHOR_TASK_COMPLETED" == false ]
do
g09 ${arr1[$SGE_TASK_ID-1]} ${arr2[$SGE_TASK_ID-1]}
let ICHOR_N_TRIES++
if [ "$ICHOR_N_TRIES" == 10 ]
then
break
fi
eval $(python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u e266b1a5-16ee-4ab8-928c-3ec4edd83626 -f check_gaussian_output "${arr1[$SGE_TASK_ID-1]}")
done

