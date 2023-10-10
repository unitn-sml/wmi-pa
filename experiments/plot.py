import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.plot import MODE_IDS, get_input_files, parse_inputs, check_values
from utils.io import check_path_exists

plt.style.use("ggplot")
fs = 18  # font size
ticks_fs = 15
lw = 2.5  # line width
figsize = (10, 8)
label_step = 5


def quantile(x, q):
    x = x.astype(np.float64)
    if np.isnan(x).all():
        return np.nan
    return np.nanquantile(x, q)


def median(x):
    return quantile(x, 0.5)


def q25(x):
    return quantile(x, 0.25)


def q75(x):
    return quantile(x, 0.75)


def median_field(field):
    return f"median_{field}"


def q25_field(field):
    return f"q25_{field}"


def q75_field(field):
    return f"q75_{field}"


def group_data(data: pd.DataFrame, cactus, timeout):
    # build a dataframe where each row is a problem and each column is a mode
    # each mode has 9 sub-columns:
    # - median time: median of the parallel_time column
    # - q25 time: 25th percentile of the parallel_time column
    # - q75 time: 75th percentile of the parallel_time column
    # - median n_integrations: median of the n_integrations column
    # - q25 n_integrations: 25th percentile of the n_integrations column
    # - q75 n_integrations: 75th percentile of the n_integrations column
    # - median error: median of the relative_error column
    # - q25 error: 25th percentile of the relative_error column
    # - q75 error: 75th percentile of the relative_error column
    data = (
        data.groupby(["problem", "mode_id"])
        .aggregate(
            median_time=("parallel_time", median),
            q25_time=("parallel_time", q25),
            q75_time=("parallel_time", q75),
            median_n_integrations=("n_integrations", median),
            q25_n_integrations=("n_integrations", q25),
            q75_n_integrations=("n_integrations", q75),
            median_error=("relative_error", median),
            q25_error=("relative_error", q25),
            q75_error=("relative_error", q75),
        )
        # every non-index cell must be np.float64
        .astype(np.float64)
        .stack(dropna=False)
        .unstack(level=(1, 2))
        .reset_index(
            drop=True,
        )
    )

    modes = data.columns.get_level_values(0).unique()
    mode_ids = [mode for mode in MODE_IDS if mode in modes]

    if cactus:
        # sort each column independently
        for param in ("time", "n_integrations", "error"):
            for mode in mode_ids:
                col_names = [median_field(param), q25_field(param), q75_field(param)]
                cols = data[mode][col_names].sort_values(
                    by=median_field(param), ignore_index=True,
                    na_position="last"
                )
                data.loc[:, (mode, col_names)] = np.nan
                data[mode].update(cols)
        # data = data.cumsum(axis=0)
        # start number of problems solved from 1
        data.index += 1
    else:
        # sort by increasing time
        sort_by = [(mode, median_field("time")) for mode in mode_ids]
        print("Sorting by", sort_by)
        data.sort_values(by=sort_by, inplace=True, ignore_index=True)
    return data


def get_modes_for_param(data, param):
    return [(mode_id, mode) for mode_id, mode in MODE_IDS.items()
            if mode_id in data.columns.get_level_values(0) and
            (param != "n_integrations" or "PA" in mode_id) and
            (param != "error" or "volesti" in mode_id)
            ]


def plot_data(outdir, data, param, xlabel, ylabel, timeout=0, frm=None, to=None, filename="", legend_pos=6, title=None):
    total_problems = max(data.index) + 1
    # crop from:to if necessary
    sfx = ""
    if frm is not None or to is not None:
        frm_i = frm or 0
        to_i = to or total_problems
        data = data[frm_i:to_i]
        sfx = "_{}_{}".format(frm_i, to_i)
    n_problems = max(data.index) + 1

    plt.figure(figsize=figsize)
    # if ylim:
    #     plt.ylim(-ylim/25, ylim)
    plt.xlim(-n_problems / 25, n_problems + n_problems / 25)

    # timeout line
    if timeout:
        x = list(range(n_problems))
        y = [timeout] * n_problems
        plt.plot(x, y, linestyle="dashed", linewidth=lw, label="timeout", color="r")

    # plot time for all modes, n_integrations only for *PA*
    modes = get_modes_for_param(data, param)

    for mode_id, mode in modes:
        plt.plot(data[mode_id][median_field(param)], color=mode.color, label=mode.label, linewidth=lw, marker="x")
        # if timeout:
        #     sup.clip(upper=timeout, inplace=True)
        sup = data[mode_id][q75_field(param)]
        inf = data[mode_id][q25_field(param)]
        plt.fill_between(data.index, sup, inf, color=mode.color, alpha=0.1)

    # legend
    plt.legend(loc=legend_pos, fontsize=fs)
    # axes labels
    plt.xlabel(xlabel, fontsize=fs)
    plt.ylabel(ylabel, fontsize=fs)
    # xticks
    positions = list(range(0, n_problems, label_step))
    labels = list(range(frm or 0, to or total_problems, label_step))

    plt.xticks(positions, labels, fontsize=ticks_fs)
    plt.yticks(fontsize=ticks_fs, rotation=0)
    plt.subplots_adjust(wspace=0.3, hspace=0.3)
    if title:
        plt.title(title, fontsize=fs)

    outfile = os.path.join(outdir, "{}_{}{}.pdf".format(param, sfx, filename))
    plt.savefig(outfile, bbox_inches="tight")
    print("created {}".format(outfile))
    plt.clf()
    csvfile = os.path.join(outdir, "{}_{}{}.csv".format(param, sfx, filename))
    csvdf = data[[(mode_id, param_q) for mode_id, _ in modes for param_q in
                  [median_field(param), q25_field(param), q75_field(param)]]]
    # flatten multiindex by joining the two levels with "_"
    csvdf.columns = ["_".join(col) for col in csvdf.columns]
    # csvdf.columns = csvdf.columns.droplevel(1)
    csvdf.to_csv(csvfile, index_label="instance")
    print("created {}".format(csvfile))


def parse_interval(interval):
    frm, to = interval.split("-")
    frm = int(frm) if frm != "" else None
    to = int(to) if to != "" else None
    return frm, to


def parse_args():
    parser = argparse.ArgumentParser(description="Plot WMI results")
    parser.add_argument("input", nargs="+", help="Folder and/or files containing result files as .json")
    parser.add_argument("-o", "--output", default=os.getcwd(), help="Output folder where to put the plots")
    parser.add_argument("-f", "--filename", default="", help="String to add to the name of the plots (optional)")
    parser.add_argument("--intervals", nargs="+", default=[],
                        help="Sub-intervals to plot in the format from-to (optional)")
    parser.add_argument("--timeout", type=int, default=0, help="Timeout line (if 0 not plotted)")
    parser.add_argument("--cactus", action="store_true", help="If true use cactus plot")
    parser.add_argument("--legend-pos", type=int, default=6, help="Legend position")
    parser.add_argument("--title", type=str, default=None, help="Title to plot")
    return parser.parse_args()


def add_relative_error(data, ref_mode="SAPASK_latte"):
    # for each problem, compute the relative error on the "value" column w.r.t. the reference mode
    # and add it as a new column
    ref_value = data[data["mode_id"] == ref_mode][["problem", "value"]]
    # merge on the problem column
    data = data.merge(ref_value, on="problem", suffixes=("", "_ref"))
    data["relative_error"] = (np.abs(data["value"] - data["value_ref"]) / data["value_ref"]).astype(np.float64)
    # drop tmp columns
    data.drop(columns=["value_ref"], inplace=True)
    return data


def main():
    args = parse_args()
    inputs = args.input
    output_dir = args.output
    intervals = args.intervals
    filename = args.filename
    timeout = args.timeout
    legend_pos = args.legend_pos
    title = args.title

    xlabel = "Problem instances"
    ylabel_time = "Query execution time (seconds)"
    ylabel_n_integrations = "Number of integrations"
    ylabel_error = "Relative error"

    check_path_exists(output_dir)

    input_files = get_input_files(inputs)
    data = parse_inputs(input_files, timeout)
    check_values(data)
    data = add_relative_error(data)

    data = group_data(data, args.cactus, args.timeout)
    # print("Grouped data:")
    # print(data)

    for interval in intervals:
        frm, to = parse_interval(interval)
        plot_data(output_dir, data, "time", xlabel, ylabel_time,
                  timeout=timeout, frm=frm, to=to, filename=filename, legend_pos=legend_pos, title=title)
        plot_data(output_dir, data, "n_integrations", xlabel, ylabel_n_integrations,
                  frm=frm, to=to, filename=filename, legend_pos=legend_pos, title=title)
        plot_data(output_dir, data, "error", xlabel, ylabel_error,
                  frm=frm, to=to, filename=filename, legend_pos=legend_pos, title=title)

    plot_data(output_dir, data, "time", xlabel, ylabel_time,
              timeout=timeout, filename=filename, legend_pos=legend_pos, title=title)
    plot_data(output_dir, data, "n_integrations", xlabel, ylabel_n_integrations,
              filename=filename, legend_pos=legend_pos, title=title)
    plot_data(output_dir, data, "error", xlabel, ylabel_error,
              filename=filename, legend_pos=legend_pos, title=title)


if __name__ == "__main__":
    main()
