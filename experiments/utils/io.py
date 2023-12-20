import argparse
import json
import sys
import os
from pysmt.shortcuts import reset_env, get_env, Bool
from wmibench.io import Density


def check_path_exists(path):
    if not os.path.exists(path):
        print("Path '{}' does not exists".format(path))
        sys.exit(1)


def check_path_not_exists(path):
    if os.path.exists(path):
        print("Path '{}' already exists".format(path))
        sys.exit(1)


def write_result(output_file, result_json):
    check_path_exists(output_file)
    with open(output_file, "r") as f:
        info = json.load(f)
    info["results"].append(result_json)

    with open(output_file, "w") as f:
        json.dump(info, f, indent=4)


def problems_from_densities(input_files):
    """Returns a list of problems from the given list of input files.

    Args:
        input_files (list): list of input files in pywmi json format.

    Yields:
        A problem for each input file. A problem is a tuple filename, index, domain, support & query, weight.
    """
    input_files = sorted(
        [f for f in input_files if os.path.splitext(f)[1] == ".json"],
        # key=lambda f: int(os.path.splitext(os.path.basename(f))[0].split('_')[2])
    )
    if len(input_files) == 0:
        print("There are no .json files in the input folder")
        sys.exit(1)

    for i, filename in enumerate(input_files):
        # reset pysmt environment
        reset_env()
        get_env().enable_infix_notation = True

        density = Density.from_file(filename)
        queries = density.queries or [Bool(True)]
        for j, query in enumerate(queries):
            print("Problem: {:>4} (query {:>4}/{:>4})/{:>4} ({:>100})".format(i + 1, j + 1, len(queries),
                                                                              len(input_files), filename),
                  end="\r", flush=True)
            support = density.support & query
            yield filename, j + 1, density.domain, support, density.weight


class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


def positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("Expected positive integer (no 0), found {}".format(value))
    return ivalue


def positive_0(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("Expected positive integer, found {}".format(value))
    return ivalue
