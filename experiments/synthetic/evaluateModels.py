import traceback
import psutil
from pysmt.shortcuts import Bool, reset_env, get_env
from wmipa import WMI
from multiprocessing import Process, Queue
from pywmi import Density
from pywmi.engines import PyXaddEngine, XsddEngine, PyXaddAlgebra
from pywmi.engines.algebraic_backend import SympyAlgebra
from pywmi.engines.xsdd import FactorizedXsddEngine as FXSDD
from pywmi.engines.xsdd.vtrees.vtree import bami, balanced


def compute_wmi(domain, support, weight, mode, cache, q):
    if "PA" in mode:
        wmi = WMI(support, weight, stub_integrate=args.stub,
                  n_threads=threads)
        res = wmi.computeWMI(Bool(True), mode=mode, cache=cache,
                             domA=set(domain.get_bool_symbols()),
                             domX=set(domain.get_real_symbols()))
        res = (*res, wmi.integrator.get_integration_time())
    else:
        if mode == "XADD":
            wmi = PyXaddEngine(
                support=support, weight=weight, domain=domain)
        elif mode == "XSDD":
            wmi = XsddEngine(support=support, weight=weight,
                             domain=domain,
                             algebra=PyXaddAlgebra(symbolic_backend=SympyAlgebra()),
                             ordered=False)
        elif mode == "FXSDD":
            wmi = FXSDD(domain,
                        support,
                        weight,
                        vtree_strategy=balanced,
                        algebra=PyXaddAlgebra(symbolic_backend=SympyAlgebra()),
                        ordered=False)

        res = (wmi.compute_volume(add_bounds=False), 0, 0)

    # it = wmi.integrator.get_integration_time()
    q.put(res)


def check_input_output(input_dir, output_dir, output_file):
    # check if input dir exists
    if not path.exists(input_dir):
        print("Folder '{}' does not exists".format(input_dir))
        sys.exit(1)

    # check if output dir exists
    if not path.exists(output_dir):
        print("Folder '{}' does not exists".format(output_dir))
        sys.exit(1)

    if output_file is not None:
        output_file = path.join(output_dir, output_file)
        if path.exists(output_file):
            print("File '{}' already exists".format(output_file))


def problems_from_densities(input_files, output_file, info):
    if output_file is None:
        problems_class = os.path.split(input_files[0])[0]
        output_name = "{}_{}_{}.json".format(
            problems_class, mode, int(time.time()))
        output_file = path.join(output_dir, output_name)
    input_files = sorted(
        [f for f in input_files if path.splitext(f)[1] == ".json"],
        # key=lambda f: int(os.path.splitext(os.path.basename(f))[0].split('_')[2])
    )
    if len(input_files) == 0:
        print("There are no .json files in the input folder")
        sys.exit(1)

    info.update({
        "params": {
            "real": None,
            "bool": None,
            "depth": None
        },
        "output_file": output_file
    })
    for i, filename in enumerate(input_files):
        try:
            # reset pysmt environment
            reset_env()
            get_env().enable_infix_notation = True
            density = Density.from_file(filename)
        except Exception as ex:
            print("Error on parsing", filename)
            # traceback.print_exception(type(ex), ex, ex.__traceback__)
            continue
        yield i+1, i+1, density.domain, density.support, density.weight
        print("\r"*200, end='')
        print("Problem: {}/{}".format(i+1, len(input_files)), end='')


# def check_vars(support_files, weight_files, reals, bools):
#     print("Checking variables")
#     for f in support_files + weight_files:
#         formula = read_smtlib(f)
#         variables = get_free_variables(formula)
#         for v in variables:
#             v_type = v.symbol_type()
#             v_name = v.symbol_name()
#             type(v_type)
#             if (v_type == BOOL and v_name not in bools) or (v_type == REAL and v_name not in reals):
#                 print("Variable '{}' in file '{}' is not present in info.json")


# def problems_from_smtlib(input_files, output_file, info):
#     support_files = sorted(
#         [f for f in input_files if path.splitext(f)[1] == ".support"])
#     weight_files = sorted(
#         [f for f in input_files if path.splitext(f)[1] == ".weight"])
#     n_support = len(support_files)
#     n_weight = len(weight_files)
#     info_file = path.join(input_dir, "info.json")
#     if n_support == 0:
#         print("There are no .support files in the input folder")
#         sys.exit(1)
#     if n_weight == 0:
#         print("There are no .weight files in the input folder")
#         sys.exit(1)
#     if not path.exists(info_file):
#         print("There is no info.json in the input folder")

#     print("Found {} supports and {} weights".format(n_support, n_weight))

#     with open(info_file, 'r') as f:
#         problems_info = json.load(f)
#         reals = problems_info["real_variables"]
#         bools = problems_info["bool_variables"]
#         depth = problems_info["depth"]

#     check_vars(support_files, weight_files, reals, bools)
#     if output_file is None:
#         output_name = "r{}_b{}_d{}_{}_{}.json".format(
#             len(reals), len(bools), depth, mode, int(time.time()))
#         output_file = path.join(output_dir, output_name)

#     info.update({
#         "params": {
#             "real": len(reals),
#             "bool": len(bools),
#             "depth": depth
#         },
#         "output_file": output_file
#     })

#     for i, s in enumerate(support_files):
#         support = read_smtlib(s)
#         domain = Domain.make(bools, reals, [])

#         for j, w in enumerate(weight_files):
#             support_filename = path.splitext(s)[0]
#             weight_filename = path.splitext(w)[0]
#             if not equals or support_filename == weight_filename:
#                 weight = read_smtlib(w)
#                 yield s, w, domain, support, weight
#                 print("\r"*100, end='')
#                 print("Support: {}/{}, Weight: {}/{}".format(i +
#                       1, n_support, j+1, n_weight), end='')


if __name__ == '__main__':
    import argparse
    import sys
    import os
    import time
    import json
    import re
    from os import path
    from pysmt.shortcuts import read_smtlib

    input_types = {
        # "smtlib": problems_from_smtlib,
        "density": problems_from_densities
    }

    modes = ["{}_cache_{}".format(m, i) for m in WMI.MODES for i in range(
        0, 4)] + WMI.MODES + ["XADD", "XSDD", "FXSDD"]

    parser = argparse.ArgumentParser(description='Compute WMI on models')
    parser.add_argument('input', help='Folder with .support and .weight files')
    parser.add_argument('-i', '--input-type', required=True,
                        help='Input type', choices=input_types.keys())
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Output folder where to save the result (default: cwd)')
    parser.add_argument('-f', '--filename',
                        help='Name of the result file (optional)')
    parser.add_argument('-m', '--mode', choices=modes,
                        required=True, help='Mode to use')
    parser.add_argument('--threads', default=None, type=int,
                        help='Number of threads to use for WMIPA')
    parser.add_argument('-e', '--equals', action='store_true',
                        help='Set this flag if you want to compute wmi only on support and weight with same name')
    parser.add_argument('-t', '--stub', action="store_true",
                        help='Set this flag if you only want to count the number of integrals to be computed')
    parser.add_argument('--timeout', type=int, default=3600,
                        help='Max time (in seconds)')

    args = parser.parse_args()

    input_dir = args.input
    input_type = args.input_type
    output_dir = args.output
    output_file = args.filename
    mode = args.mode
    equals = args.equals
    timeout = args.timeout
    threads = args.threads

    check_input_output(input_dir, output_dir, output_file)

    elements = [path.join(input_dir, f) for f in os.listdir(input_dir)]
    files = [e for e in elements if path.isfile(e)]

    print("Started computing")
    time_start = time.time()
    results = []
    info = {}
    input_fn = input_types[input_type]
    for s, w, domain, support, weight in input_fn(files, output_file, info):
        cache = -1
        if "cache" in mode:
            cache = int(mode.split("_")[2])

        time_init = time.time()
        q = Queue()
        timed_proc = Process(
            target=compute_wmi, args=(domain,
                                      support,
                                      weight,
                                      mode.split("_")[0],
                                      cache,
                                      q),
        )
        timed_proc.start()
        timed_proc.join(timeout)
        if timed_proc.is_alive():
            res = (None, None, timeout)
            time_total = timeout

            # kill the process and its children
            pid = timed_proc.pid
            proc = psutil.Process(pid)
            for subproc in proc.children(recursive=True):
                try:
                    subproc.kill()
                except psutil.NoSuchProcess:
                    continue
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass
        else:
            res = q.get()
            time_total = time.time() - time_init

        value, n_integrations, integration_time = res

        res = {
            "support": s,
            "weight": w,
            "value": value,
            "n_integrations": n_integrations,
            "time": time_total,
            "integration_time": integration_time
        }
        results.append(res)

    print()
    print("Computed {} WMI".format(len(results)))

    info.update({
        "mode": mode,
        "results": results
    })
    output_file = info.pop("output_file")

    with open(output_file, 'w') as f:
        json.dump(info, f, indent=4)
    print("Created {}".format(output_file))

    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))
