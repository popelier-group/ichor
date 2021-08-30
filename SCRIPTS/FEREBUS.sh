#!/bin/bash -l
#$ -o /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/OUTPUTS
#$ -e /home/mfbx4mb9/work/WATER/v3/.DATA/SCRIPTS/ERRORS
#$ -pe mp 4
#$ -wd /home/mfbx4mb9/work/WATER/v3
#$ -t 1-3
export OMP_NUM_THREADS=4
export OMP_PROC_BIND=true
ICHOR_DATFILE=/home/mfbx4mb9/work/WATER/v3/.DATA/JOBS/DATAFILES/fb3f3a5c-1e4c-4d80-896f-9257cc1d3ad2
arr1=()
while IFS=, read -r var1
do
    arr1+=($var1)
done < $ICHOR_DATFILE

pushd ${arr1[$SGE_TASK_ID-1]}
  /home/mfbx4mb9/work/WATER/v3/PROGRAMS/FEREBUS
popd
python /home/mfbx4mb9/src/ICHOR-v3/ichor3.py -c config.properties -u fb3f3a5c-1e4c-4d80-896f-9257cc1d3ad2 -f move_models "${arr1[$SGE_TASK_ID-1]}"

