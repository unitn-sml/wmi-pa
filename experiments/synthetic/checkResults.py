import argparse
import json
import math
import os
import sys
from collections import defaultdict
from os import path


def get_inputs(inputs):
    input_files = []
    for inp in inputs:
        if not path.exists(inp):
            print("'{}' input does not exist".format(inp))
            sys.exit(1)
        if path.isfile(inp):
            _, ext = path.splitext(inp)
            if ext == ".json":
                input_files.append(inp)
            else:
                print("'{}' is not a .json file".format(inp))
                sys.exit(1)
        elif path.isdir(inp):
            inp_files = [path.join(inp, f) for f in os.listdir(inp)]
            for f in inp_files:
                if path.isfile(f):
                    _, ext = path.splitext(f)
                    if ext == ".json":
                        input_files.append(f)

    if len(input_files) <= 0:
        print("No .json file found")
        sys.exit(1)

    input_files = sorted(input_files)

    print("Files found:\n\t{}".format("\n\t".join(input_files)))
    return input_files


def get_results(input_files):
    wmi_results = defaultdict(dict)  # {(support, weight): {mode: value}}

    # for every input
    for f in input_files:
        with open(f) as json_file:
            data = json.load(json_file)
            mode = data['mode']
            # print(data['results'])
            for res in data['results']:
                support = res['support']
                weight = res['weight']
                value = res['value']
                wmi_results[(support, weight)][mode] = value
    return wmi_results


def check_results(wmi_results):
    for problem, results in wmi_results.items():
        target = results['PA']
        assert all(map(lambda x: math.isclose(x, target), results.values())), \
            "Problem found in {}: {}".format(problem, results)


def main():
    parser = argparse.ArgumentParser(description='Plot WMI results')
    parser.add_argument(
        'input', nargs='+', help='Folder and/or files containing result files as .json')
    args = parser.parse_args()
    inputs = args.input
    # get all .json files
    input_files = get_inputs(inputs)

    # results = {}
    wmi_results = get_results(input_files)
    check_results(wmi_results)
    print("Ok!")


if __name__ == '__main__':
    main()
