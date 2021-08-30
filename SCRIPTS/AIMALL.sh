#!/bin/bash -l
#$ -o /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/OUTPUTS
#$ -e /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/ERRORS
#$ -j y
#$ -wd /home/mfbx4mb9/work/WATER/v3
#$ -S /bin/bash
#$ -pe mp 2
SGE_TASK_ID=1
export OMP_NUM_THREADS=2
export OMP_PROC_BIND=true
ICHOR_DATFILE=/home/mfbx4mb9/work/WATER/v3/.DATA/JOBS/DATAFILES/d14550a9-8fa5-4422-b25a-b0df06710f5e
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

aimall_test -nogui -usetwoe=0 -atoms=all -encomp=3 -boaq=gs30 -iasmesh=fine -nproc=2 -naat=2 ${arr1[$SGE_TASK_ID-1]} &> ${arr2[$SGE_TASK_ID-1]}
let ICHOR_N_TRIES++
if [ "$ICHOR_N_TRIES" == 10 ]
then
break
fi
eval $(python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u d14550a9-8fa5-4422-b25a-b0df06710f5e -f check_aimall_output "${arr1[$SGE_TASK_ID-1]}")
done

