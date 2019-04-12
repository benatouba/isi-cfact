#!/bin/bash
#
#SBATCH --qos=priority
#SBATCH --partition=priority
##SBATCH --constraint=broadwell
#SBATCH --job-name=tas
#SBATCH --account=isipedia
#SBATCH --output=output/tas.out
#SBATCH --error=output/tas.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=bschmidt@pik-potsdam.de

# # block one node completely to get all its memory.
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --exclusive
echo 'Available memory of node is:'
cat /proc/meminfo | grep MemFree | awk '{ print $2 }'
source /home/bschmidt/.programs/anaconda3/bin/activate detrending
# srun bash preprocessing/merge_data.sh
# srun python3 preprocessing/create_test_data.py
srun python3 run_regression.py
srun python3 fitting.py
# run next line for profiling memory
# srun mprof run --include-children --multiprocess run_regression_classic.py
