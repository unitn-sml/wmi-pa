import traceback
import psutil
from pysmt.shortcuts import Bool, reset_env, get_env
from wmipa import WMI
from multiprocessing import Process, Queue
from pywmi import Density
from pywmi.engines import PyXaddEngine, XsddEngine, PyXaddAlgebra
import argparse
import sys
import os
import time
import json
from os import path


def compute_wmi(domain, support, weight, mode, cache, threads, stub, q):
    if "PA" in mode:
        wmi = WMI(support, weight, stub_integrate=stub,
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
                             domain=domain, factorized=False,
                             algebra=PyXaddAlgebra(), ordered=False)

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


def problems_from_densities(input_files):
    input_files = sorted(
        [f for f in input_files if path.splitext(f)[1] == ".json"],
        # key=lambda f: int(os.path.splitext(os.path.basename(f))[0].split('_')[2])
    )
    if len(input_files) == 0:
        print("There are no .json files in the input folder")
        sys.exit(1)

    for i, filename in enumerate(input_files):
        print(i+1, filename)
        try:
            # reset pysmt environment
            reset_env()
            get_env().enable_infix_notation = True
            density = Density.from_file(filename)
        except Exception as ex:
            print("Error on parsing", filename)
            # traceback.print_exception(type(ex), ex, ex.__traceback__)
            continue
        yield filename, density.domain, density.support, density.weight
        print("\r"*200, end='')
        print("Problem: {}/{}".format(i+1, len(input_files)), end='')


def parse_args():
    modes = ["{}_cache_{}".format(m, i) for m in WMI.MODES for i in range(
        0, 4)] + WMI.MODES + ["XADD", "XSDD"]

    parser = argparse.ArgumentParser(description='Compute WMI on models')
    parser.add_argument('input', help='Folder with .json files')
    # parser.add_argument('-i', '--input-type', required=True,
    #                     help='Input type', choices=input_types.keys())
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Output folder where to save the result (default: cwd)')
    parser.add_argument('-f', '--filename',
                        help='Name of the result file (optional)')
    parser.add_argument('-m', '--mode', choices=modes,
                        required=True, help='Mode to use')
    parser.add_argument('--threads', default=None, type=int,
                        help='Number of threads to use for WMIPA')
    # parser.add_argument('-e', '--equals', action='store_true',
    #                     help='Set this flag if you want to compute wmi only on support and weight with same name')
    parser.add_argument('-t', '--stub', action="store_true",
                        help='Set this flag if you only want to count the number of integrals to be computed')
    parser.add_argument('--timeout', type=int, default=3600,
                        help='Max time (in seconds)')

    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = args.input
    # input_type = args.input_type
    output_dir = args.output
    output_file = args.filename
    mode = args.mode
    # equals = args.equals
    timeout = args.timeout
    threads = args.threads
    stub = args.stub

    check_input_output(input_dir, output_dir, output_file)
    output_file = output_file or "{}_{}_{}.json".format(
        os.path.split(input_dir.rstrip('/'))[1], mode, int(time.time()))
    output_file = path.join(output_dir, output_file)

    elements = [path.join(input_dir, f) for f in os.listdir(input_dir)]
    files = [e for e in elements if path.isfile(e)]

    print("Started computing")
    time_start = time.time()
    results = []

    for filename, domain, support, weight in problems_from_densities(files):
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
                                      threads, 
                                      stub,
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
            "filename": filename,
            "value": value,
            "n_integrations": n_integrations,
            "time": time_total,
            "integration_time": integration_time
        }
        results.append(res)

    print()
    print("Computed {} WMI".format(len(results)))

    info = {
        "mode": mode,
        "results": results
    }

    with open(output_file, 'w') as f:
        json.dump(info, f, indent=4)
    print("Created {}".format(output_file))

    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))


if __name__ == '__main__':
    main()
