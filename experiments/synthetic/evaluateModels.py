import psutil
from pysmt.shortcuts import Bool, reset_env, get_env
from wmipa import WMI
from wmipa.volesti_integrator import VolestiIntegrator
from wmipa.latte_integrator import LatteIntegrator
from multiprocessing import Process, Queue
from queue import Empty as EmptyQueueError
from pywmi import Density
from pywmi.engines import PyXaddEngine, XsddEngine, PyXaddAlgebra, RejectionEngine
from pywmi.engines.algebraic_backend import SympyAlgebra
from pywmi.engines.xsdd import FactorizedXsddEngine as FXSDD
from pywmi.engines.xsdd.vtrees.vtree import balanced

import argparse
import sys
import os
import time
import json
from os import path


def compute_wmi(domain, support, weight, args, q):
    if "PA" in args.mode:
        integrator = LatteIntegrator if args.integration == "latte" else VolestiIntegrator
        wmi = WMI(support, weight, integrator=integrator, **args.__dict__)
        res = wmi.computeWMI(
            Bool(True),
            mode=args.mode,
            cache=args.cache,
            domA=set(domain.get_bool_symbols()),
            domX=set(domain.get_real_symbols()),
        )
        res = (*res, wmi.integrator.get_integration_time())
    else:
        if args.mode == "XADD":
            wmi = PyXaddEngine(support=support, weight=weight, domain=domain)
        elif args.mode == "XSDD":
            wmi = XsddEngine(
                support=support,
                weight=weight,
                domain=domain,
                algebra=PyXaddAlgebra(symbolic_backend=SympyAlgebra()),
                ordered=False,
            )
        elif args.mode == "FXSDD":
            wmi = FXSDD(
                domain,
                support,
                weight,
                vtree_strategy=balanced,
                algebra=PyXaddAlgebra(symbolic_backend=SympyAlgebra()),
                ordered=False,
            )
        elif args.mode == "Rejection":
            wmi = RejectionEngine(domain, support, weight, sample_count=100000)
        else:
            raise ValueError(f"Invalid mode {args.mode}")

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
        try:
            # reset pysmt environment
            reset_env()
            get_env().enable_infix_notation = True
            density = Density.from_file(filename)
        except Exception as ex:
            print("Error on parsing", filename)
            # traceback.print_exception(type(ex), ex, ex.__traceback__)
            continue
        queries = density.queries or [Bool(True)]
        for j, query in enumerate(queries):
            print("\r" * 300, end="")
            print(
                "Problem: {} (query {}/{})/{} ({})".format(i + 1, j + 1, len(queries), len(input_files), filename),
                end="",
            )
            support = density.support & query
            yield filename, j + 1, density.domain, support, density.weight


def write_result(mode, res, output_file):
    if not os.path.exists(output_file):
        info = {"mode": mode, "results": [res]}
    else:
        with open(output_file, "r") as f:
            info = json.load(f)
        info["results"].append(res)

    with open(output_file, "w") as f:
        json.dump(info, f, indent=4)


def parse_args():
    modes = WMI.MODES + ["XADD", "XSDD", "FXSDD", "Rejection"]

    parser = argparse.ArgumentParser(
        description="Compute WMI on models", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("input", help="Folder with .json files")
    # parser.add_argument('-i', '--input-type', required=True,
    #                     help='Input type', choices=input_types.keys())
    parser.add_argument(
        "-o", "--output", default=os.getcwd(), help="Output folder where to save the result (default: cwd)"
    )
    parser.add_argument("-f", "--filename", help="Name of the result file (optional)")
    parser.add_argument("-m", "--mode", choices=modes, required=True, help="Mode to use")
    parser.add_argument("--threads", default=None, type=int, help="Number of threads to use for WMIPA")
    parser.add_argument("--timeout", type=int, default=3600, help="Max time (in seconds)")
    parser.add_argument("-c", "--cache", choices=[-1, 0, 1, 2, 3], default=-1, help="Cache level for WMIPA methods")
    parser.add_argument(
        "-t",
        "--stub",
        action="store_true",
        help="Set this flag if you only want to count the number of integrals to be computed",
    )
    integration_parsers = parser.add_subparsers(
        title="integration",
        description="Type of integration to use",
        dest="integration",
    )
    latte_parser = integration_parsers.add_parser("latte", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    volesti_parser = integration_parsers.add_parser("volesti", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    volesti_parser.add_argument("-e", "--error", default=0.1, type=float, help="Relative error acceptable [in (0, 1)]")
    volesti_parser.add_argument(
        "--algorithm",
        choices=VolestiIntegrator.ALGORITHMS,
        default=VolestiIntegrator.DEF_ALGORITHM,
        help=f"Volume computation method: {', '.join(VolestiIntegrator.ALGORITHMS)}",
    )
    volesti_parser.add_argument(
        "--walk_type",
        choices=VolestiIntegrator.RANDOM_WALKS,
        default=VolestiIntegrator.DEF_RANDOM_WALK,
        help="Type of random walk: {', '.join(VolestiIntegrator.RANDOM_WALKS)}",
    )
    volesti_parser.add_argument("-N", type=int, default=VolestiIntegrator.DEF_N, help="Number of samples")
    volesti_parser.add_argument(
        "--walk_length",
        type=int,
        default=VolestiIntegrator.DEF_WALK_LENGTH,
        help="Length of random walk (0 for default value)",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    # input_type = args.input_type
    output_file = args.filename
    long_mode = args.mode
    if "PA" in args.mode:
        long_mode += "_" + args.integration
        if args.cache > -1:
            long_mode += "_cache_" + str(args.cache)
    # equals = args.equals

    check_input_output(args.input, args.output, args.filename)
    output_file = output_file or "{}_{}_{}.json".format(
        os.path.split(args.input.rstrip("/"))[1], long_mode, int(time.time())
    )
    output_file = path.join(args.output, output_file)
    print("Creating... {}".format(output_file))

    elements = [path.join(args.input, f) for f in os.listdir(args.input)]
    files = [e for e in elements if path.isfile(e)]

    print("Started computing, mode: ", long_mode)
    time_start = time.time()

    for i, (filename, query_n, domain, support, weight) in enumerate(problems_from_densities(files)):

        time_init = time.time()
        q = Queue()

        timed_proc = Process(
            target=compute_wmi,
            args=(domain, support, weight, args, q),
        )
        timed_proc.start()
        timed_proc.join(args.timeout)
        if timed_proc.is_alive():
            res = (None, None, args.timeout)
            time_total = args.timeout

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
            try:
                res = q.get(block=False)
                time_total = time.time() - time_init
            except EmptyQueueError:
                # killed because of exceeding resources
                res = (None, None, args.timeout)
                time_total = args.timeout

        value, n_integrations, integration_time = res
        res = {
            "filename": filename,
            "query": query_n,
            "value": value,
            "n_integrations": n_integrations,
            "time": time_total,
            "integration_time": integration_time,
        }
        write_result(long_mode, res, output_file)

    print()
    print("Computed {} WMI".format(i + 1))

    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))


if __name__ == "__main__":
    main()
