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



def group_data(data: pd.DataFrame, cactus, timeout):
    # build a dataframe where each row is a problem and each column is a mode
    # each mode has 4 sub-columns:
    # - time: the average time to solve the problem (in seconds)
    # - stdtime: the standard deviation of the time
    # - n_integrations: the average number of integrations performed
    # - stdn_integrations: the standard deviation of the number of integrations
    data = (
        data.groupby(["problem", "mode_id"])
        .aggregate(
            time=("parallel_time", "mean"),
            stdtime=("parallel_time", "std"),
            n_integrations=("n_integrations", "mean"),
            stdn_integrations=("n_integrations", "std"),
        )
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
        for param in ("time", "n_integrations"):
            for mode in mode_ids:
                stdcolname = "std{}".format(param)
                cols = data[mode][[param, stdcolname]].sort_values(
                    by=param, ignore_index=True
                )
                # stdcol = data[mode][stdcolname].sort_values(by=param, ignore_index=True)
                # meancol = data[mode][param].sort_values(ignore_index=True)
                # meancol.where(meancol < timeout, inplace=True)

                # meancol.columns = pd.MultiIndex.from_tuples([(mode, param)])
                data[(mode, param)] = np.NaN
                data[(mode, param)].update(cols[param])
                data[(mode, stdcolname)] = np.NaN
                data[(mode, stdcolname)].update(cols[stdcolname])

        # data = data.cumsum(axis=0)
        # start number of problems solved from 1
        data.index += 1
    else:
        # sort by increasing time
        sort_by = [(mode, "time") for mode in modes]
        data.sort_values(by=sort_by, inplace=True, ignore_index=True)
    return data


def plot_data(outdir, data, param, xlabel, timeout=0, frm=None, to=None, filename="", legend_pos=6, title=None):
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
    modes = [(mode_id, mode) for mode_id, mode in MODE_IDS.items()
             if mode_id in data.columns.get_level_values(0) and
             (param == "time" or "PA" in mode_id)]

    for mode_id, mode in modes:
        plt.plot(data[mode_id][param], color=mode.color, label=mode.label, linewidth=lw, marker="x")
        # stddev
        stdcol = "std{}".format(param)
        sup = data[mode_id][param] + data[mode_id][stdcol]
        if timeout:
            sup.clip(upper=timeout, inplace=True)

        inf = (data[mode_id][param] - data[mode_id][stdcol]).clip(lower=0)
        plt.fill_between(data.index, sup, inf, color=mode.color, alpha=0.1)

    if param == "time":
        ylabel = "Query execution time (seconds)"
    else:
        ylabel = "Number of integrations"

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
    csvdf = data[[(mode_id, param) for mode_id, _ in modes]]
    csvdf.columns = csvdf.columns.droplevel(1)
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

    check_path_exists(output_dir)

    input_files = get_input_files(inputs)
    data = parse_inputs(input_files, timeout)
    check_values(data)

    data = group_data(data, args.cactus, args.timeout)
    # print("Grouped data:")
    # print(data)

    for interval in intervals:
        frm, to = parse_interval(interval)
        plot_data(
            output_dir,
            data,
            "parallel_time",
            xlabel,
            timeout=timeout,
            frm=frm,
            to=to,
            filename=filename,
            legend_pos=legend_pos,
            title=title,
        )
        plot_data(
            output_dir,
            data,
            "n_integrations",
            xlabel,
            frm=frm,
            to=to,
            filename=filename,
            legend_pos=legend_pos,
            title=title,
        )

    plot_data(
        output_dir,
        data,
        "time",
        xlabel,
        timeout=timeout,
        filename=filename,
        legend_pos=legend_pos,
        title=title,
    )
    plot_data(
        output_dir,
        data,
        "n_integrations",
        xlabel,
        filename=filename,
        legend_pos=legend_pos,
        title=title,
    )


if __name__ == "__main__":
    main()
