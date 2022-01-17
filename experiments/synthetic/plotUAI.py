import argparse
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TIMEOUT = 3600


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
        if mode == "PANL":
            continue

        params = result_out["params"]
        for result in result_out["results"]:
            result["time"] = min(result["time"], TIMEOUT)
            if result["time"] == TIMEOUT:
                result["n_integrations"] = 0
                if "integration_time" in result:
                    result["integration_time"] = TIMEOUT
            # assert result["time"] >= result["integration_time"]
            result["mode"] = mode
            result.update(params)
        data.extend(result_out["results"])

    data = pd.DataFrame(data)

    modes = (data["mode"].unique())
    sort_by = [("time", mode)
               for mode in ["PA", "PAEUF", "PAEUFTA"]
               if mode in modes]
    # groupby to easily generate MulitIndex
    data = data. \
        groupby(["support", "weight", "mode"]). \
        aggregate({
            "time": "sum",
            "n_integrations": "sum",
            "value": "sum",
            # "integration_time": "sum"
        }). \
        unstack()
    data['time'] = data['time'].fillna(TIMEOUT)
    data['n_integrations'] = data['n_integrations'].fillna(0)
    data.sort_values(by=sort_by, inplace=True)
    return data


def plot_data(outdir, data, param, unit=None, timeout=None, frm=None, to=None):
    total_problems = len(data)
    if frm is not None and to is not None:
        data = data[frm:to]
        sfx = "_{}_{}".format(frm, to)
    elif frm is not None:
        data = data[frm:]
        sfx = "_{}_{}".format(frm, total_problems)
    elif to is not None:
        data = data[:to]
        sfx = "_{}_{}".format(0, to)
    else:
        sfx = ""

    title = "{}{}".format(param, sfx)

    ax = data[param]. \
        plot(title=title,
             x_compat=True,
             grid=True,
             figsize=(10, 8))
    # axes labels
    ax.set_xlabel('Problem')
    ylabel = param if not unit else "{} ({})".format(param, unit)
    ax.set_ylabel(ylabel)
    # xticks
    n_problems = len(data)
    positions = list(range(0, n_problems, 50))
    labels = list(range(frm or 0, to or total_problems, 50))
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)

    if timeout is not None:
        x = list(range(n_problems))
        y = [timeout] * n_problems
        plt.plot(x,
                 y,
                 linestyle="dashed",
                 label="timeout")
    ax.legend(loc="center left", title="Mode")
    outfile = os.path.join(outdir, "{}_uai{}.png".format(param, sfx))
    plt.savefig(outfile)
    print("created {}".format(outfile))


def check_values(data):
    ii = data["time", "PA"] < TIMEOUT

    for mode in data.columns.get_level_values(1).unique():
        diff = ~np.isclose(data[ii]["value", mode].values,
                           data[ii]["value", "PA"].values)
        if diff.any():
            error("Error! {} values of {} do not match with PA".format(
                diff.sum(), mode))


def parse_interval(interval):
    frm, to = interval.split("-")
    frm = int(frm) if frm != "" else None
    to = int(to) if to != "" else None

    return frm, to


def main(args):
    inputs = args.input
    output_dir = args.output
    intervals = args.intervals

    if not os.path.exists(output_dir):
        error("Output folder '{}' does not exists".format(output_dir))

    input_files = get_input_files(inputs)
    data = parse_inputs(input_files)
    check_values(data)
    for interval in intervals:
        frm, to = parse_interval(interval)
        plot_data(output_dir, data, "time", "s", frm=frm, to=to)
        plot_data(output_dir, data, "n_integrations", frm=frm, to=to)

    plot_data(output_dir, data, "time", "s", timeout=TIMEOUT)
    plot_data(output_dir, data, "n_integrations")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot WMI results')
    parser.add_argument(
        'input', nargs='+', help='Folder and/or files containing result files as .json')
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Output folder where to put the plots (default: cwd)')
    parser.add_argument('--intervals', nargs='+', default=[],
                        help='Sub-intervals to plot in the format from-to')
    main(parser.parse_args())
