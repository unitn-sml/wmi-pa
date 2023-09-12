import argparse
import os
import re
from typing import List, Tuple

import pandas as pd

from utils.io import check_path_exists
from utils.plot import get_input_files, parse_inputs

re_filename_to_info = re.compile(r"r(\d+)_b\d+_d\d+_pd(\d+)_s\d+_\d+.json")

ROW_PARAMS = {"nreals": ("\# reals", int), "pd": ("polynomial degree", int)}
COL_PARAMS = {"integrator_error": ("$\epsilon$", float), "integrator_N": ("N", int)}


def pair(arg):
    lst = arg.split("=")
    if len(lst) != 2:
        raise argparse.ArgumentTypeError("Pair must be of the form x=y")
    var, val = lst
    if var in ROW_PARAMS:
        return var, ROW_PARAMS[var][1](val)
    elif var in COL_PARAMS:
        return var, COL_PARAMS[var][1](val)
    else:
        raise argparse.ArgumentTypeError("Unknown variable {}".format(var))


def filename_to_nreals(filename: str) -> int:
    return int(re_filename_to_info.match(filename).group(1))


def filename_to_pd(filename: str) -> int:
    return int(re_filename_to_info.match(filename).group(2))


def add_problem_info(data: pd.DataFrame):
    data["nreals"] = data["filename"].apply(filename_to_nreals)
    data["pd"] = data["filename"].apply(filename_to_pd)
    return data


def filter_data(data: pd.DataFrame, fix: List[Tuple], ref="SAPASK_latte"):
    for var, val in fix:
        print(f"Filtering {var}={val} ({type(val)})")
        print(f"Values of {var}: {data[var].value_counts()}")
        data = data[(data[var] == val) | (data["mode_id"] == ref)]
        print(f"{len(data)} rows left")
    return data


def avg_error_table(data: pd.DataFrame, outdir, filename, rows_var, cols_var, fix, ref="SAPASK_latte"):
    # build a dataframe where each row is a problem and each column is a mode
    # each mode has 3 sub-columns:
    # - avg_error: the average relative error
    # - std_error: the standard deviation of the relative error
    # - avg_value: the average value of the problem
    reference_value = data[data["wmi_id"] == ref][["problem", "value"]]
    data = pd.merge(data, reference_value, on=["problem"], suffixes=("", "_ref"))
    data["relative_error"] = (data["value"] - data["value_ref"]).abs() / data["value_ref"]

    data = (
        data.groupby(["problem", rows_var, cols_var])
        .aggregate(
            avg_error=("relative_error", "mean"),
            std_error=("relative_error", "std"),
            avg_value=("value", "mean"),
        )
        .dropna(subset=["avg_error"])
        .stack(dropna=False)
        .unstack(level=(2, 3))
        # .reset_index(drop=True)
        .reset_index()
    )

    # aggregate by rows_var and compute mean of avg_error and std_error
    modes = [m for m in data.columns.get_level_values(0).unique() if m not in ["problem", rows_var]]
    agg_fn = {(mode, moment): "mean" for mode in modes for moment in ["avg_error", "std_error"]}
    data = data.groupby(rows_var)
    data = data.agg(agg_fn).round(2).reset_index()

    # prettify table:
    # 1. for each mode replace avg_error and std_error with avg_error +- std_error
    for mode in modes:
        new_col = '$' + data[(mode, 'avg_error')].astype(str) + ' \pm ' + data[(mode, 'std_error')].astype(str) + '$'
        data.drop(columns=[mode], inplace=True, level=0)
        data[mode] = new_col

    # 2. rename each column (different from rows_var) to <cols_var>=<col_name>
    cols_var_pretty = COL_PARAMS[cols_var][0]
    data.columns = [f"{cols_var_pretty}={col_name}" if col_name != rows_var else col_name for col_name, _ in
                    data.columns]

    # 3. rename rows_var to its pretty name
    data.rename(columns={rows_var: ROW_PARAMS[rows_var][0]}, inplace=True)

    # 4. table caption and label
    fixed_volesti_param = ",".join(
        f"{COL_PARAMS[p][0]}={v}" for p, v in fix if p.startswith("integrator_"))
    fixed_problem_param = ",".join(
        f"{ROW_PARAMS[p][0]}={v}" for p, v in fix if not p.startswith("integrator_"))
    caption = (f"Average error of \\method{{}}(VolEsti) with {fixed_volesti_param} "
               f"on problems with {fixed_problem_param}.")
    label = f"tab:avg_error{filename}"

    # save table
    data.to_latex(os.path.join(outdir, f"avg_error_table_{rows_var}{filename}.tex"), caption=caption, label=label,
                  escape=False, column_format="c" * len(data.columns), multicolumn_format="c", index=False)


def parse_args():
    parser = argparse.ArgumentParser(description="Plot WMI results for approximated integration")
    parser.add_argument("input", nargs="+", help="Folder and/or files containing result files as .json")
    parser.add_argument("-o", "--output", default=os.getcwd(), help="Output folder where to put the plots")
    parser.add_argument("-f", "--filename", default="", help="String to add to the name of the plots (optional)")
    parser.add_argument("--fix", type=pair, nargs="+", default=[],
                        help="Fix the y-axis to the given values (e.g. --fix integrator_error=0.1)")
    parser.add_argument("--rows-var", choices=ROW_PARAMS.keys(), required=True, help="Variable row")
    parser.add_argument("--cols-var", choices=COL_PARAMS.keys(), required=True, help="Variable column")
    return parser.parse_args()


def main():
    args = parse_args()
    inputs = args.input
    output_dir = args.output
    timeout = 0
    assert args.rows_var not in (fix[0] for fix in args.fix), "Cannot fix the row variable"
    assert args.cols_var not in (fix[0] for fix in args.fix), "Cannot fix the column variable"
    check_path_exists(output_dir)

    input_files = get_input_files(inputs)
    data = parse_inputs(input_files, timeout)
    data = add_problem_info(data)
    data = filter_data(data, args.fix)
    avg_error_table(data, output_dir, args.filename, args.rows_var, args.cols_var, args.fix,
                    ref="SAPASK_latte")


if __name__ == "__main__":
    main()
