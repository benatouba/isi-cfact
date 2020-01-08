import subprocess
from pathlib import Path

output_base = Path("/p/tmp/mengel/isimip/isi-cfact/input/")

dataset = "GSWP3"
qualifier = "_sub20"

outdir = output_base/dataset

def d(var):
    return str(outdir/var)+"_"+dataset.lower()+qualifier+".nc4 "

p = "module load cdo && cdo -O "

cmd = p+"chname,tasmax,tasrange -sub "+d("tasmax")+d("tasmin")+d("tasrange")
print(cmd)
subprocess.check_call(cmd, shell=True)
cmd = p+"sub "+d("tas")+d("tasmin")+d("tasskewtemp")
print(cmd)
subprocess.check_call(cmd, shell=True)
cmd = p+"chname,tas,tasskew -div "+d("tasskewtemp")+d("tasrange")+d("tasskew")
print(cmd)
subprocess.check_call(cmd, shell=True)

