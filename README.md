# ISI-CFACT

ISI-CFACT produces counterfactual climate data from past datasets for the ISIMIP project.

## Idea
Counterfactual climate is a hypothetical climate in a world without climate change.
For impact models, such climate should stay as close as possible to the observed past,
as we aim to compare impact events of the past (for which we have data) to the events in the counterfactual. The difference is a proxy for the impact of climate change. We run the following steps:

1. We approximate the change in past climate through a model with three parts. Long-term trend, an ever-repeating yearly cycle, and a trend in the yearly cycle. Trends are induced by global mean temperature change. We use a Bayesian approach to estimate all parameters of the model and their dependencies at once, here implemented through pymc3. Yearly cycle and trend in yearly cycles are approximated through a finite number of modes, which are periodic in the year. The parameter distributions tell us which part of changes in the variables can be explained through global mean temperature as a direct driver.

2. We subtract the estimated trends from to global mean temperature change from the observed data. This provides a counterfactual, which comes without the trends easily explained by global mean temperature change.


The following graph illustrates the approach. Grey is the original data, red is our estimation of change. Blue is the original data minus the parts that were estimated to driven by global mean temperature change.

![Counterfactual example](image01.png)

## Usage

This code is currently taylored to run on the supercomputer at the Potsdam Institute for Climate Impact Research. Generalizing it into a package is ongoing work.

Adjust `settings.py`

For estimating parameter distributions (above step 1) and smaller datasets

`python run_bayes_reg.py`

For larger datasets adjust `submit.sh` and

`sbatch submit.sh`

For producing counterfactuals (above step 2)

`python run_detrending.py`

## Install

We use the `from mpi4py.futures import MPIPoolExecutor` to distribute jobs via MPI. We needed the intel-optimized python libraries to make this work with `theano`. The configuration is very much tailored to the PIK supercomputer at the moment. Please do

conda config --add channels intel

conda env create --name pymc3 -f config/environment.yml

You may also optionally

`cp config/theanorc ~/.theanorc`

## Credits

The code on Bayesian estimation of parameters in timeseries with periodicity in PyMC3 is inspired and adopted from [Ritchie Vink's](https://www.ritchievink.com) [post](https://www.ritchievink.com/blog/2018/10/09/build-facebooks-prophet-in-pymc3-bayesian-time-series-analyis-with-generalized-additive-models/) on Bayesian timeseries analysis with additive models.

## License

This code is licensed under GPLv3, see the LICENSE.txt. See commit history for authors.

