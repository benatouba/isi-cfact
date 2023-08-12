#!/bin/bash
#### merge files after passed sanity checks  ####

tile=$1
traces_or_ts=$2

#SBATCH --qos=short # for smaller tiles
#SBATCH --partition=standard   # for smaller tiles
###SBATCH --partition=largemem  # for large tiles
#SBATCH --job-name=attrici_merge_files
#SBATCH --account=dmcci
#SBATCH --output=/p/tmp/annabu/projects/attrici/log/merge_files_%A_%x.log
#SBATCH --error=/p/tmp/annabu/projects/attrici/log/merge_files_%x.log
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=annabu@pik-potsdam.de
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --time=00-02:00:00


# merge trace and ts files for each variable after they passed sanity checks
for var in tas0 tas6 tas12; do
#for var in tas0 tas6 tas12 tasrange pr0 pr6 pr12 pr18 sfcWind rsds hurs; do  
#for var in tas0 tas6 tas12 tas18 tasrange tasskew pr0 pr6 pr12 pr18 sfcWind rsds hurs; do  
  echo "Merging: " ${var}
  /home/annabu/.conda/envs/attrici_pymc5_2/bin/python -u sanity_check/merge_files.py ${tile} ${traces_or_ts} ${var}
done

echo "Finished, merged all" ${trace_or_ts}