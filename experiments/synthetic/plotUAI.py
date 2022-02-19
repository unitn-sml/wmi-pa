import argparse
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TIMEOUT = 3600
plt.style.use("ggplot")
fs = 15  # font size
ticks_fs = 15
lw = 2.5  # line width
figsize = (10, 8)
label_step = 10
COLORS = {
    "PA": "#E24A33",
    "PAEUFTA": "#988ED5",
    "XSDD": "#348ABD",
    "FXSDD": "#554348",
    "XADD": "#093A3E",
    "Rejection": "#FBC15E",
    "PA_cache_2": "#8EBA42",
    "other4": "#FFB5B8"
}
ORDER = ["XADD", "XSDD", "FXSDD", "PA", "PA_cache_2", "PAEUF", "PAEUFTA"]
ERR_TOLERANCE = 5e-2  # absolute tolerance on value mismatch


def error(msg=""):
    print(msg)
    sys.exit(1)


def get_input_files(input_dirs):
    input_files = []
    for input_dir in input_dirs:
        if not os.path.exists(input_dir):
            error("Input folder '{}' does not exists".format(input_dir))
        for filename in os.listdir(input_dir):
            filepath = os.path.join(input_dir, filename)
            if os.path.isfile(filepath):
                _, ext = os.path.splitext(filepath)
                if ext == ".json":
                    input_files.append(filepath)
    if not input_files:
        error("No .json file found")
    input_files = sorted(input_files)
    print("Files found:\n\t{}".format("\n\t".join(input_files)))
    return input_files


def parse_inputs(input_files):
    data = []
    for filename in input_files:
        with open(filename) as f:
            result_out = json.load(f)
        mode = result_out["mode"]

        for result in result_out["results"]:
            result["mode"] = mode
        data.extend(result_out["results"])

    # groupby to easily generate MulitIndex
    data = pd.DataFrame(data)

    # deal with missing values and timeouts
    data["time"] = data["time"].clip(upper=TIMEOUT)

    # do not plot n_integrations where mode times out or where not available
    data["n_integrations"] = data["n_integrations"].where(
        # (data["time"] < TIMEOUT) & (data["time"].notna()) &
        (data["n_integrations"] > 0),
        pd.NA)

    return data


def plot_data(outdir, data, param, xlabel, timeout=None, frm=None, to=None, filename=""):
    total_problems = len(data)
    # crop from:to if necessary
    sfx = ""
    if frm is not None or to is not None:
        frm_i = frm or 0
        to_i = to or total_problems
        data = data[frm_i:to_i]
        sfx = "_{}_{}".format(frm_i, to_i)
    n_problems = len(data)

    plt.figure(figsize=figsize)

    # timeout line
    if timeout is not None:
        x = list(range(n_problems))
        y = [timeout] * n_problems
        plt.plot(x, y,
                 linestyle="dashed",
                 linewidth=lw,
                 label="timeout",
                 color="r")

    # plot time for all modes, n_integrations only for *PA*
    modes = data.columns.get_level_values(0).unique()
    modes = [mode for mode in ORDER if mode in modes]
    modes = [mode for mode in modes if param == "time" or "PA" in mode]
    for mode in modes:
        plt.plot(data[mode][param], color=COLORS[mode],
                 label=mode, linewidth=lw, marker="x")
        # stddev
        stdcol = "std{}".format(param)
        sup = (data[mode][param] + data[mode][stdcol])
        if param == "time":
            sup.clip(upper=TIMEOUT, inplace=True)
        inf = (data[mode][param] - data[mode][stdcol]).clip(lower=0)
        plt.fill_between(range(n_problems), sup, inf,
                         color=COLORS[mode], alpha=0.1)

    if param == "time":
        ylabel = "Query execution time (seconds)"
    else:
        ylabel = "Number of integrations"

    # legend
    plt.legend(loc="center left", fontsize=fs)
    # axes labels
    plt.xlabel(xlabel, fontsize=fs)
    plt.ylabel(ylabel, fontsize=fs)
    # xticks
    n_problems = len(data)
    positions = list(range(0, n_problems, label_step))
    labels = list(range(frm or 0, to or total_problems, label_step))
    plt.xticks(positions, labels, fontsize=ticks_fs)
    plt.yticks(fontsize=ticks_fs, rotation=0)
    plt.subplots_adjust(wspace=0.3, hspace=0.3)

    outfile = os.path.join(
        outdir, "{}_uai{}{}.png".format(param, sfx, filename))
    plt.savefig(outfile)
    print("created {}".format(outfile))
    plt.clf()


def check_values(data, ref="PAEUFTA"):
    data = data \
        .groupby(["filename", "query", "mode"]) \
        .aggregate(
            time=("time", "min"),
            value=("value", "min"),
            count=("time", "count")) \
        .unstack()

    # ensure we have at most one output foreach (filename, query, mode) combination
    assert ((data["count"] == 1) |
            (data["count"].isna())).all().all(), "Some output are duplicated"

    # print(data.reset_index()[["time", "value"]])

    # check values match with the reference mode "ref" (where not NaN)
    ii = data["value", ref].notna()
    for mode in data.columns.get_level_values(1).unique():
        indexes = ii & data["value", mode].notna()
        # check if results agree with PAEUFTA with an absolute tolerance of ERR_TOLERANCE
        diff = ~np.isclose(data[indexes]["value", mode].values,
                           data[indexes]["value", ref].values, atol=ERR_TOLERANCE)
        if diff.any():
            print("Error! {}/{} values of {} do not match with {}".format(
                diff.sum(), indexes.sum(), mode, ref))
            print(data[indexes][diff][["value"]])
        else:
            print("Mode {:10s}: {:4d} values OK".format(
                mode, indexes.sum()))


def parse_interval(interval):
    frm, to = interval.split("-")
    frm = int(frm) if frm != "" else None
    to = int(to) if to != "" else None
    return frm, to


def group_data(data, cactus):
    # aggregate and compute the mean for each query
    data = data \
        .groupby(["filename", "mode"]) \
        .aggregate(
            time=("time", "mean"),
            stdtime=("time", "std"),
            n_integrations=("n_integrations", "mean"),
            stdn_integrations=("n_integrations", "std")) \
        .unstack() \
        .swaplevel(0, 1, axis=1) \
        .sort_index(axis=1) \
        .reset_index(drop=True)

    modes = data.columns.get_level_values(0).unique()
    modes = [mode for mode in ORDER if mode in modes]
    if cactus:
        # sort each column independently
        for param in ("time", "n_integrations"):
            for mode in modes:
                stdcol = "std{}".format(param)
                cols = data[mode][[param, stdcol]].sort_values(
                    by=param, ignore_index=True)
                data.loc[:][mode][[param, stdcol]] = cols
               
        # print(data["PAEUFTA"])
    else:
        # sort by increasing time
        sort_by = [(mode, "time") for mode in modes]
        data.sort_values(by=sort_by, inplace=True, ignore_index=True)
    return data


def parse_args():
    parser = argparse.ArgumentParser(description="Plot WMI results")
    parser.add_argument(
        "input", nargs="+", help="Folder and/or files containing result files as .json")
    parser.add_argument("-o", "--output", default=os.getcwd(),
                        help="Output folder where to put the plots (default: cwd)")
    parser.add_argument("-f", "--filename", default="",
                        help="String to add to the name of the plots (optional)")
    parser.add_argument("--intervals", nargs="+", default=[],
                        help="Sub-intervals to plot in the format from-to (optional)")
    parser.add_argument("--no-timeout", action="store_true",
                        help="If true timeout line is not plotted")
    parser.add_argument("--cactus", action="store_true",
                        help="If true use cactus plot")
    return parser.parse_args()


def main():
    args = parse_args()
    inputs = args.input
    output_dir = args.output
    intervals = args.intervals
    filename = args.filename
    timeout = None if args.no_timeout else TIMEOUT

    if args.cactus:
        xlabel = "Number of problems solved"
    else:
        xlabel = "Problem instances"

    if not os.path.exists(output_dir):
        error("Output folder '{}' does not exists".format(output_dir))

    input_files = get_input_files(inputs)
    data = parse_inputs(input_files)
    check_values(data)
    data = group_data(data, args.cactus)

    for interval in intervals:
        frm, to = parse_interval(interval)
        plot_data(output_dir, data, "time", xlabel,
                  frm=frm, to=to, filename=filename)
        plot_data(output_dir, data, "n_integrations", xlabel,
                  frm=frm, to=to, filename=filename)

    plot_data(output_dir, data, "time", xlabel,
              timeout=timeout, filename=filename)
    plot_data(output_dir, data, "n_integrations", xlabel, filename=filename)


if __name__ == "__main__":
    main()
