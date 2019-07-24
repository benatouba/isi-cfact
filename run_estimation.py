import os
import numpy as np
import netCDF4 as nc
from datetime import datetime
from pathlib import Path
import settings as s
import sys

sys.path.append("..")
import idetrend.estimator as est
import idetrend.datahandler as dh

try:
    submitted = os.environ["SUBMITTED"] == "1"
    task_id = int(os.environ["SLURM_ARRAY_TASK_ID"])
    njobarray = int(os.environ["SLURM_ARRAY_TASK_COUNT"])
    s.ncores_per_job = 1
    s.progressbar = False
except KeyError:
    submitted = False
    njobarray = 1
    task_id = 0
    s.progressbar = True

dh.create_output_dirs(s.output_dir)

gmt_file = os.path.join(s.input_dir, s.gmt_file)
ncg = nc.Dataset(gmt_file, "r")
gmt = np.squeeze(ncg.variables["tas"][:])
ncg.close()

# get data to detrend
to_detrend_file = os.path.join(s.input_dir, s.source_file)
obs_data = nc.Dataset(to_detrend_file, "r")
nct = obs_data.variables["time"]
lats = obs_data.variables["lat"][:]
lons = obs_data.variables["lon"][:]
ncells = len(lats) * len(lons)

if ncells % njobarray:
    print("task_id", task_id)
    print("njobarray", njobarray)
    print("ncells", ncells)
    raise ValueError("ncells does not fit into array job, adjust jobarray.")

calls_per_arrayjob = ncells / njobarray

# Calculate the starting and ending values for this task based
# on the SLURM task and the number of runs per task.
start_num = int(task_id * calls_per_arrayjob)
end_num = int((task_id + 1) * calls_per_arrayjob - 1)

# Print the task and run range
print("This is SLURM task", task_id, "which will do runs", start_num, "to", end_num)

estimator = est.estimator(s)

TIME0 = datetime.now()

for n in np.arange(start_num, end_num + 1, 1, dtype=np.int):
    i = int(n % len(lats))
    j = int(n / len(lats))
    lat, lon = lats[i], lons[j]
    print("This is SLURM task", task_id, "run number", n, "lat,lon", lat, lon)

    data = obs_data.variables[s.variable][:, i, j]
    df = dh.create_dataframe(nct, data, gmt)

    # only run detrending, if at least FIXME:
    # [enter amount and decide what to do when less are available] data points are available in timeseries

    # if df["y"].size == np.sum(df["y"].isna()):
    #     print("All data NaN, probably ocean, skip.")
    # else:
    trace = estimator.estimate_parameters(df, lat, lon)
    df_with_cfact = estimator.estimate_timeseries(df, trace)
    dh.save_to_csv(df_with_cfact, s, lat, lon)

obs_data.close()

print(
    "Estimation completed for all cells. It took {0:.1f} minutes.".format(
        (datetime.now() - TIME0).total_seconds() / 60
    )
)