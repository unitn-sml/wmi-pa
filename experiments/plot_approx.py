import argparse
import os
import re
from typing import List, Tuple

import pandas as pd

from utils.io import check_path_exists
from utils.plot import get_input_files, parse_inputs

re_filename_to_info = re.compile(r"models_r(\d+)_b\d+_d\d+_pd(\d+)_s\d+_\d+.json")

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


def filter_data(data: pd.DataFrame, fix: List[Tuple], ref="SAE4WMI_latte"):
    for var, val in fix:
        data = data[(data[var] == val) | (data["mode_id"] == ref)]
    return data


def quantile(q):
    return lambda x: x.quantile(q)


def avg_table(cols_var, data, filename, fix, outdir, rows_var, agg_field, pretty_agg_field):
    # build a dataframe where each row is a problem and each column is a mode
    # each mode has 3 sub-columns:
    # - avg_error: the average agg_field
    # - std_error: the standard deviation of the agg_field
    data = (
        data.groupby(["problem", rows_var, cols_var])
        .aggregate(
            avg_agg_field=(agg_field, "mean"),
            # std_agg_field=(agg_field, "std"),
            # avg_value=("value", "mean"),
        )
        .dropna(subset=["avg_agg_field"])
        .stack(dropna=False)
        .unstack(level=(2, 3))
        # .reset_index(drop=True)
        .reset_index()
    )
    # print(data)
    # aggregate by rows_var and compute 1st, 2nd and 3rd quartiles of avg_agg_field
    modes = [m for m in data.columns.get_level_values(0).unique() if m not in ["problem", rows_var]]
    # agg_fn = {(mode, moment): "mean" for mode in modes for moment in ["avg_agg_field", "std_agg_field"]}
    quantiles = [0.25, 0.5, 0.75]
    agg_fn = {(mode, "avg_agg_field"): [quantile(x) for x in quantiles] for mode in modes}

    data = data.groupby(rows_var)
    # for group in data:
    #     print(group)
    data = data.agg(agg_fn).round(2).reset_index()
    # prettify table:
    # 1. for each mode replace avg_agg_field and std_agg_field with avg_agg_field +- std_agg_field
    # for mode in modes:
    # new_col = '$' + data[(mode, 'avg_agg_field')].astype(str) + ' \pm ' + data[(mode, 'std_agg_field')].astype(
    #     str) + '$'
    # data.drop(columns=[mode], inplace=True, level=0)
    # data[mode] = new_col
    # for each mode, create one column for each quantile
    # drop level 1 (moment)
    data.columns = data.columns.droplevel(level=1)

    # sort columns alphabetically
    data = data[sorted(data.columns, key=lambda x: x if x[0] != rows_var else (0,))]

    # 2. rename each column (different from rows_var) to <cols_var>=<col_name>
    cols_var_pretty = COL_PARAMS[cols_var][0]
    rows_var_pretty = ROW_PARAMS[rows_var][0]
    new_cols = []
    for col_name in data.columns.get_level_values(0).unique():
        if col_name == rows_var:
            new_cols.append((col_name,))
        else:
            for q in quantiles:
                new_cols.append((f"{cols_var_pretty}={col_name}", f"$q_{{{q}}}$"))
    # new_cols = [(f"{cols_var_pretty}={col_name}", f"$q_{q}")
    #             if col_name != rows_var else col_name
    #             for col_name, _ in data.columns
    #             for q in quantiles
    #             ]
    # remake a multiindex
    data.columns = pd.MultiIndex.from_tuples(new_cols)
    # 3. rename rows_var to its pretty name
    data.rename(columns={rows_var: rows_var_pretty}, inplace=True)
    print(data)

    # 4. table caption and label
    fixed_volesti_param = ",".join(
        f"{COL_PARAMS[p][0]}={v}" for p, v in fix if p.startswith("integrator_"))
    fixed_problem_param = ",".join(
        f"{ROW_PARAMS[p][0]}={v}" for p, v in fix if not p.startswith("integrator_"))
    k = 10  # TODO: compute k from data
    caption = (f"{pretty_agg_field.capitalize()} of \\method{{}}(VolEsti) with {fixed_volesti_param} "
               f"on problems with {fixed_problem_param}."
               f"For each problem, we compute the average {pretty_agg_field} over {k} random seeds."
               f"For each set of problems, the table shows the 1st, 2nd and 3rd quartiles of the {pretty_agg_field}.")
    label = f"tab:avg_{agg_field}{filename}"
    # save table
    data.to_latex(os.path.join(outdir, f"avg_{agg_field}_table_{rows_var}{filename}.tex"), caption=caption, label=label,
                  escape=False, column_format="c" * len(data.columns), multicolumn_format="c", index=False)


def avg_error_table(data: pd.DataFrame, outdir, filename, rows_var, cols_var, fix, ref="SAE4WMI_latte"):
    reference_value = data[data["wmi_id"] == ref][["problem", "value"]]
    data = pd.merge(data, reference_value, on=["problem"], suffixes=("", "_ref"))
    # data["relative_error"] = (data["value"] - data["value_ref"]).abs() / data["value_ref"]
    data["relative_error"] = (data["value"] - data["value_ref"]).abs() / data["value_ref"]

    # print the data where nreals=8, integrator_N=1000000 and relative_error > 0.1.
    # print the columns: filename, value, value_ref, relative_error and those starting with integrator_
    # print(data[(data["nreals"] == 8) & (data["integrator_N"] == 1000000) & (data["relative_error"] > 0.1)][
    #           ["filename", "value", "value_ref", "relative_error", "integrator_N", "integrator_error", "integrator_seed"]])

    avg_table(cols_var, data, filename, fix, outdir, rows_var, "relative_error", "relative error")


def avg_time_gain_table(data: pd.DataFrame, outdir, filename, rows_var, cols_var, fix, ref="SAE4WMI_latte"):
    reference_value = data[data["wmi_id"] == ref][["problem", "sequential_integration_time"]]
    data = pd.merge(data, reference_value, on=["problem"], suffixes=("", "_ref"))
    data["relative_time_gain"] = (data["sequential_integration_time_ref"] - data["sequential_integration_time"]) / data[
        "sequential_integration_time_ref"]
    # data["relative_time_gain"] = (data["sequential_time"]) / data["sequential_time_ref"]

    avg_table(cols_var, data, filename, fix, outdir, rows_var, "relative_time_gain", "relative speedup")


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
                    ref="SAE4WMI_latte")
    avg_time_gain_table(data, output_dir, args.filename, args.rows_var, args.cols_var, args.fix,
                        ref="SAE4WMI_latte")


if __name__ == "__main__":
    main()
