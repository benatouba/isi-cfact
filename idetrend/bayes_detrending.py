import os
import theano
import numpy as np
import pymc3 as pm
import matplotlib.pylab as plt
import pandas as pd
import netCDF4 as nc
from datetime import datetime
from pathlib import Path


class bayes_regression(object):
    def __init__(self, regressor, cfg):

        self.regressor = regressor.values
        self.output_dir = cfg.output_dir
        self.init = cfg.init
        self.draws = cfg.draws
        self.cores = cfg.ncores_per_job
        self.chains = cfg.chains
        self.tune = cfg.tune
        self.progressbar = cfg.progressbar
        self.days_of_year = cfg.days_of_year

        self.modes = cfg.modes
        self.linear_mu = cfg.linear_mu
        self.linear_sigma = cfg.linear_sigma
        self.sigma_beta = cfg.sigma_beta
        self.smu = cfg.smu
        self.sps = cfg.sps
        self.stmu = cfg.stmu
        self.stps = cfg.stps

    def setup_model(self, df):

        # create instance of pymc model class
        self.model = pm.Model()

        with self.model:
            slope = pm.Normal("slope", self.linear_mu, self.linear_sigma)
            intercept = pm.Normal("intercept", self.linear_mu, self.linear_sigma)
            sigma = pm.HalfCauchy("sigma", self.sigma_beta, testval=1)

        x_yearly = self.add_season_model(
            df, self.modes, smu=self.smu, sps=self.sps, beta_name="beta_yearly"
        )
        x_trend = self.add_season_model(
            df, self.modes, smu=self.stmu, sps=self.stps, beta_name="beta_trend"
        )

        with self.model as model:

            estimated = (
                model["intercept"]
                + model["slope"] * self.regressor
                + det_dot(x_yearly, model["beta_yearly"])
                + (self.regressor * det_dot(x_trend, model["beta_trend"]))
            )
            out = pm.Normal(
                "obs", mu=estimated, sd=model["sigma"], observed=df["y_scaled"]
            )

        self.x_yearly = x_yearly
        self.x_trend = x_trend
        self.df = df
        return self.model, (x_yearly, x_trend)

    def run(self, datazip):

        df, i, j = datazip
        self.setup_model(df)

        output_dir = self.output_dir / "traces" / ("trace_" + str(i) + "_" + str(j))

        print("Search for trace in", output_dir)
        self.trace = pm.load_trace(output_dir, model=self.model)

        try:
            for var in ["slope", "intercept", "beta_yearly", "beta_trend", "sigma"]:
                if var not in self.trace.varnames:
                    raise IndexError("Sample data not completely saved. Rerun.")
            print("Successfully loaded sampled data. Skip this for sampling.")
        except IndexError:
            self.sample()
            self.save_trace(i, j)

        trend_post, year_trend_post, posterior = self.estimate_timeseries()

        self.estimate_counterfactual(trend_post, year_trend_post)

        return self.df

    def sample(self):

        TIME0 = datetime.now()

        with self.model:
            self.trace = pm.sample(
                draws=self.draws,
                init=self.init,
                cores=self.cores,
                chains=self.chains,
                tune=self.tune,
                progressbar=self.progressbar,
            )

        TIME1 = datetime.now()
        print(
            "Finished job {0} in {1:.0f} seconds.".format(
                os.getpid(), (TIME1 - TIME0).total_seconds()
            )
        )

        return self.trace

    def add_season_model(self, df, modes, smu, sps, beta_name):
        """
        Creates a model of periodic data in time by using
        a fourier series with specified number of modes.
        :param data:
        """

        # rescale the period, as t is also scaled
        p = 365.25 / (df["ds"].max() - df["ds"].min()).days
        x = fourier_series(df["t"], p, modes)

        with self.model:
            beta = pm.Normal(beta_name, mu=smu, sd=sps, shape=2 * modes)
        return x  # , beta

    def estimate_timeseries(self):

        trend_post = (
            self.trace["intercept"] + self.trace["slope"] * self.regressor[:, None]
        )

        year_post = det_seasonality_posterior(self.trace["beta_yearly"], self.x_yearly)
        year_trend_post = det_seasonality_posterior(
            self.trace["beta_trend"], self.x_trend
        )

        post = y_inv(trend_post + year_post + year_trend_post, self.df["y"])

        trend_post = y_inv(trend_post, self.df["y"])
        year_post = y_inv(year_post, self.df["y"]) - self.df["y"].min()
        year_trend_post = y_inv(year_trend_post, self.df["y"]) - self.df["y"].min()

        return trend_post, year_trend_post, post

    def estimate_counterfactual(self, trend_post, year_trend_post):

        self.df["cfact"] = self.df["y"].data - (
            trend_post + year_trend_post - trend_post[0]
        ).mean(axis=1)

        return self.df

    def save_trace(self, i, j):

        output_dir = self.output_dir / "traces" / ("trace_" + str(i) + "_" + str(j))
        pm.backends.save_trace(self.trace, output_dir, overwrite=True)


def det_dot(a, b):
    """
    The theano dot product and NUTS sampler don't work with large matrices?

    :param a: (np matrix)
    :param b: (theano vector)
    """
    return (a * b[None, :]).sum(axis=-1)


def det_seasonality_posterior(beta, x):
    return np.dot(x, beta.T)


def fourier_series(t, p, n):
    # 2 pi n / p
    x = 2 * np.pi * np.arange(1, n + 1) / p
    # 2 pi n / p * t
    x = x * t[:, None]
    x = np.concatenate((np.cos(x), np.sin(x)), axis=1)
    return x


def det_trend(k, m, delta, t, s, A):
    return (k + np.dot(A, delta)) * t + (m + np.dot(A, (-s * delta)))


def y_norm(y_to_scale, y_orig):
    return (y_to_scale - y_orig.min()) / (y_orig.max() - y_orig.min())


def y_inv(y, y_orig):
    """rescale data y to y_original"""
    return y * (y_orig.max() - y_orig.min()) + y_orig.min()


def create_dataframe(nct, data_to_detrend, gmt):

    # proper dates plus additional time axis that is
    # from 0 to 1 for better sampling performance

    ds = pd.to_datetime(
        nct[:], unit="D", origin=pd.Timestamp(nct.units.lstrip("days since"))
    )
    t_scaled = (ds - ds.min()) / (ds.max() - ds.min())
    gmt_on_data_cal = np.interp(t_scaled, np.linspace(0, 1, len(gmt)), gmt)
    gmt_scaled = y_norm(gmt_on_data_cal, gmt_on_data_cal)
    y_scaled = y_norm(data_to_detrend, data_to_detrend)

    tdf = pd.DataFrame(
        {
            "ds": ds,
            "t": t_scaled,
            "y": data_to_detrend,
            "y_scaled": y_scaled,
            "gmt": gmt_on_data_cal,
            "gmt_scaled": gmt_scaled,
        }
    )

    return tdf


def mcs_helper(nct, data_to_detrend, gmt, variable, i, j):

    data = data_to_detrend.variables[variable][:, i, j]
    df = create_dataframe(nct, data, gmt)
    return (df, i, j)
