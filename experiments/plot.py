import argparse
import json
import os
import sys
from collections import namedtuple, OrderedDict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.run import get_wmi_id
from utils.io import check_path_exists
from wmipa import WMI
from wmipa.integration import LatteIntegrator, SymbolicIntegrator, VolestiIntegrator

plt.style.use("ggplot")
fs = 18  # font size
ticks_fs = 15
lw = 2.5  # line width
figsize = (10, 8)
label_step = 5


def wmi_id_to_mode_id(wmi_id):
    if "volesti" in wmi_id:
        fields = wmi_id.split("_")
        # remove seed (second last field)
        fields = fields[:-2] + fields[-1:]
        return "_".join(fields)
    return wmi_id


def get_mode_id(mode, integrator):
    return wmi_id_to_mode_id(get_wmi_id(mode, integrator))


COLORS = ["#2f4f4f", "#7f0000", "#006400", "#4b0082", "#ff0000", "#00ff00", "#1e90ff", "#00ffff", "#f4a460", "#0000ff",
          "#d8bfd8", "#ff00ff", "#ffff54", "#00fa9a", "#ff69b4"]

ModeIdInfo = namedtuple("ModeIdInfo", ["color", "label"])

# Mode id sorted by order of appearance in the legend
MODE_IDS = OrderedDict([
    (get_mode_id("XADD", None), ModeIdInfo(COLORS[0], "XADD")),
    (get_mode_id("XSDD", None), ModeIdInfo(COLORS[1], "XSDD")),
    (get_mode_id("FXSDD", None), ModeIdInfo(COLORS[2], "FXSDD")),
    (get_mode_id(WMI.MODE_PA, LatteIntegrator()), ModeIdInfo(COLORS[3], "WMI-PA")),
    (get_mode_id(WMI.MODE_SA_PA, LatteIntegrator()), ModeIdInfo(COLORS[4], "SA-WMI-PA")),
    (get_mode_id(WMI.MODE_SA_PA_SK, LatteIntegrator()), ModeIdInfo(COLORS[5], "SA-WMI-PA-SK")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.1, N=1000)),
     ModeIdInfo(COLORS[6], "SA-WMI-PA-SK(VolEsti, error=0.1, N=1000)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.05, N=1000)),
     ModeIdInfo(COLORS[7], "SA-WMI-PA-SK(VolEsti, error=0.05, N=1000)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.01, N=1000)),
     ModeIdInfo(COLORS[8], "SA-WMI-PA-SK(VolEsti, error=0.01, N=1000)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.01, N=10000)),
     ModeIdInfo(COLORS[11], "SA-WMI-PA-SK(VolEsti, error=0.01, N=10000)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.01, N=100000)),
     ModeIdInfo(COLORS[12], "SA-WMI-PA-SK(VolEsti, error=0.01, N=100000)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.01, N=1000000)),
     ModeIdInfo(COLORS[13], "SA-WMI-PA-SK(VolEsti, error=0.01, N=1000000)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.005, N=1000)),
     ModeIdInfo(COLORS[9], "SA-WMI-PA-SK(VolEsti, error=0.005)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, SymbolicIntegrator()),
     ModeIdInfo(COLORS[10], "SA-WMI-PA-SK(Symbolic)")),
])

ERR_TOLERANCE = 1e-1  # absolute tolerance on value mismatch


def get_input_files(input_paths):
    input_files = []
    input_paths = list(reversed(input_paths))
    while input_paths:
        input_path = input_paths.pop()
        check_path_exists(input_path)
        if os.path.isdir(input_path):
            input_paths.extend([os.path.join(input_path, f) for f in os.listdir(input_path)])
            continue
        assert os.path.isfile(input_path)
        _, ext = os.path.splitext(input_path)
        if ext == ".json":
            input_files.append(input_path)

    if not input_files:
        raise ValueError("No .json files found in the input folder")
    input_files = sorted(input_files)
    print("Files found:\n\t{}".format("\n\t".join(input_files)))
    return input_files


def parse_inputs(input_files, timeout):
    data = []
    for filename in input_files:
        with open(filename) as f:
            result_out = json.load(f)
        mode = result_out["mode"]
        wmi_id = result_out["wmi_id"]
        if "cache" in mode:
            continue
        for result in result_out["results"]:
            result["mode"] = mode
            result["wmi_id"] = wmi_id
        data.extend(result_out["results"])

    data = pd.DataFrame(data)

    data["mode_id"] = data["wmi_id"].apply(wmi_id_to_mode_id)
    data["filename"] = data["filename"].apply(os.path.basename)
    data["problem"] = data["filename"] + data["query"].apply(str)

    # deal with missing values and timeouts
    if timeout:
        data["parallel_time"] = data["parallel_time"].clip(upper=timeout)

    # set n_integrations = NaN where mode times out or where not available, so that they are not plotted
    data["n_integrations"] = data["n_integrations"].where(
        (data["parallel_time"] < timeout)
        & (data["parallel_time"].notna())
        & (data["n_integrations"] > 0),
        pd.NA,
    )

    return data


def check_values(data: pd.DataFrame, ref="SAPASK_latte"):
    """Check if the values of the different modes match with the reference mode "ref" (where not NaN)

    """

    data = (
        data.groupby(["problem", "wmi_id"])
        .aggregate(time=("parallel_time", "first"),
                   value=("value", "first"),
                   count=("parallel_time", "count"))
        .unstack()
    )

    # ensure we have no duplicated output
    assert (data["count"] == 1).all().all(), "Some output are duplicated"

    # check values match with the reference mode "ref" (where not NaN)
    ii = data["value", ref].notna()
    for mode in data.columns.get_level_values(1).unique():
        indexes = ii & data["value", mode].notna()
        # check if results agree with "ref" with a relative tolerance of ERR_TOLERANCE.
        # TODO: maybe we should check using the integrator_error instead of ERR_TOLERANCE, but currently we cannot
        #  trust the guarantees given by VolEsti.
        diff = ~np.isclose(
            data[indexes]["value", mode].values,
            data[indexes]["value", ref].values,
            rtol=ERR_TOLERANCE,
        )
        if diff.any():
            print("Error! {}/{} values of {} do not match with {}".format(diff.sum(), indexes.sum(), mode, ref))
            # print(data[indexes][diff]["value"][[ref, mode]])
        else:
            print("Mode {:10s}: {:4d} values OK".format(mode, indexes.sum()))


def plot_avg_error(data: pd.DataFrame, outdir, filename, ref="SAPASK_latte"):
    # build a dataframe where each row is a problem and each column is a mode
    # each mode has 3 sub-columns:
    # - avg_error: the average relative error
    # - std_error: the standard deviation of the relative error
    # - avg_value: the average value of the problem
    reference_value = data[data["wmi_id"] == ref][["problem", "value"]]
    data = pd.merge(data, reference_value, on=["problem"], suffixes=("", "_ref"))
    data["relative_error"] = (data["value"] - data["value_ref"]).abs() / data["value_ref"]
    data = (
        data.groupby(["problem", "mode_id"])
        .aggregate(
            avg_error=("relative_error", "mean"),
            std_error=("relative_error", "std"),
            avg_value=("value", "mean"),
        )
        .dropna(subset=["avg_error"])
        .stack(dropna=False)
        .unstack(level=(1, 2))
        .reset_index(drop=True)
    )

    # sort the problems using as key the maximum avg_error considering all modes.
    modes = [(mode_id, mode) for mode_id, mode in MODE_IDS.items() if
             mode_id in data.columns.get_level_values(0).unique() and mode_id != ref]
    data["max_avg_error"] = data[[(mode_id, "avg_error") for mode_id, _ in modes]].max(axis=1)
    data = data.sort_values(by="max_avg_error", ascending=True, ignore_index=True)

    # for each mode, plot the average relative error on each problem (with error bars)
    fig, ax = plt.subplots(figsize=(10, 5))
    for mode_id, mode in modes:
        data_mode = data[mode_id]
        # plot with error bars
        data_mode["avg_error"].plot(
            ax=ax,
            label=mode.label,
            color=mode.color,
            marker="x",
            linestyle="",
            yerr=data_mode["std_error"],
            capsize=4,
            alpha=0.7,
        )
    ax.set_ylabel("Average relative error")
    ax.set_xlabel("Problem")
    ax.set_xticks(range(len(data)))
    ax.legend()
    plt.tight_layout()
    outfile = os.path.join(outdir, "error{}.png".format(filename))
    plt.savefig(outfile, bbox_inches="tight")

    # data.columns = data.columns.map(lambda x: (MODE_IDS[x[0]].label, x[1]) if x[0] in MODE_IDS else x)
    # print(data)


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
        sort_by = [(mode, "parallel_time") for mode in modes]
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

    plot_avg_error(data, output_dir, filename)

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
