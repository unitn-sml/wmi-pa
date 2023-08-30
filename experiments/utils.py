import json
import os
import random
import sys
from multiprocessing import Queue, Process
from os import path
from queue import Empty as EmptyQueueError

import psutil
from pysmt.shortcuts import Bool, reset_env, get_env, Real
from pywmi import PyXaddEngine, XsddEngine, PyXaddAlgebra, FactorizedXsddEngine as FXSDD, RejectionEngine, Density
from pywmi.engines.algebraic_backend import SympyAlgebra
from pywmi.engines.xsdd.vtrees.vtree import balanced

from wmipa import WMI
from wmipa.integration import LatteIntegrator, VolestiIntegrator, SymbolicIntegrator

from collections import namedtuple

WMIResult = namedtuple("WMIResult", ["wmi_id",
                                     "value",
                                     "n_integrations",
                                     "parallel_integration_time",
                                     "sequential_integration_time"])


def get_wmi_id(mode, integrator):
    integrator_str = "" if integrator is None else f"_{integrator.to_short_str()}"
    return f"{mode}{integrator_str}"


def check_input_output(input_dir, output_dir, output_file):
    if not path.exists(input_dir):
        print("Folder '{}' does not exists".format(input_dir))
        sys.exit(1)

    if not path.exists(output_dir):
        print("Folder '{}' does not exists".format(output_dir))
        sys.exit(1)

    if output_file is not None:
        output_file = path.join(output_dir, output_file)
        if path.exists(output_file):
            print("File '{}' already exists".format(output_file))


def get_output_filename(output_dir, input_dir, wmi_id, run_id):
    return path.join(output_dir, f"{input_dir}_{wmi_id}_{run_id}.json")


def initialize_output_files(args, input_dir, run_id):
    """Initializes output files for each mode and integrator.

    Args:
        args: command line arguments
        input_dir: Input directory
        run_id: Run ID

    Returns:
        A dictionary mapping each wmi_id (identifying a pair <mode, integrator>) to the corresponding output file
    """
    output_files = {}
    for integrator in get_integrators(args):
        wmi_id = get_wmi_id(args.mode, integrator)
        output_filename = get_output_filename(args.output, input_dir, wmi_id, run_id)
        with open(output_filename, "w") as output_file:
            skeleton = {
                "wmi_id": wmi_id,
                "mode": args.mode,
                "integrator": integrator.to_json(),
                "results": []
            }
            json.dump(skeleton, output_file)
        output_files[wmi_id] = output_filename
    return output_files


def write_result(output_file, result_json):
    if not os.path.exists(output_file):
        raise FileNotFoundError(f"File {output_file} does not exist")
    with open(output_file, "r") as f:
        info = json.load(f)
    info["results"].append(result_json)

    with open(output_file, "w") as f:
        json.dump(info, f, indent=4)


def get_integrators(args):
    """Returns the integrators to be used for the given command line arguments."""
    if "PA" not in args.mode:
        raise ValueError(f"Cannot get integrator for mode {args.mode}")
    if args.integration == "latte":
        return [LatteIntegrator(n_threads=args.n_threads, stub_integrate=args.stub)]
    elif args.integration == "volesti":
        seeds = list(range(args.seed, args.seed + args.n_seeds))
        return [VolestiIntegrator(n_threads=args.n_threads, stub_integrate=args.stub,
                                  algorithm=args.algorithm, error=args.error, walk_type=args.walk_type,
                                  walk_length=args.walk_length, seed=seed, N=args.N) for seed in seeds]
    elif args.integration == "symbolic":
        return [SymbolicIntegrator(n_threads=args.n_threads, stub_integrate=args.stub)]
    else:
        raise ValueError(f"Invalid integrator {args.integrator}")


def compute_wmi(args, domain, support, weight, q):
    """Computes the WMI for the given domain, support and weight, using the mode define by args. The result is put in
    the queue q to be retrieved by the main process.
    """

    if args.unweighted:
        weight = Real(1)

    if "PA" in args.mode:
        integrators = get_integrators(args)
        wmi = WMI(support, weight, integrator=integrators)
        results, n_ints = wmi.computeWMI(
            Bool(True),
            mode=args.mode,
            cache=args.cache,
        )
        res = []
        for result, n_int, integrator in zip(results, n_ints, integrators):
            wmi_id = get_wmi_id(args.mode, integrator)
            wmi_result = WMIResult(wmi_id=wmi_id,
                                   value=float(result),
                                   n_integrations=int(n_int),
                                   parallel_integration_time=integrator.get_parallel_integration_time(),
                                   sequential_integration_time=integrator.get_sequential_integration_time())
            res.append(wmi_result)
    else:
        if args.mode == "XADD":
            wmi = PyXaddEngine(domain=domain, support=support, weight=weight)
        elif args.mode == "XSDD":
            wmi = XsddEngine(
                domain=domain,
                support=support,
                weight=weight,
                algebra=PyXaddAlgebra(symbolic_backend=SympyAlgebra()),
                ordered=False,
            )
        elif args.mode == "FXSDD":
            wmi = FXSDD(
                domain=domain,
                support=support,
                weight=weight,
                vtree_strategy=balanced,
                algebra=PyXaddAlgebra(symbolic_backend=SympyAlgebra()),
                ordered=False,
            )
        elif args.mode == "Rejection":
            wmi = RejectionEngine(domain, support, weight, sample_count=10 ** 6)
        else:
            raise ValueError(f"Invalid mode {args.mode}")

        res = [WMIResult(wmi_id=get_wmi_id(args.mode, None),
                         value=wmi.compute_volume(add_bounds=False),
                         n_integrations=None,
                         parallel_integration_time=0,
                         sequential_integration_time=0)]

    q.put(res)


def compute_wmi_with_timeout(args, domain, support, weight):
    """Run compute_wmi with a timeout. If the computation exceeds the timeout, a TimeoutError is raised."""
    q = Queue()
    timed_proc = Process(
        target=compute_wmi,
        args=(args, domain, support, weight, q),
    )
    timed_proc.start()
    timed_proc.join(args.timeout)
    if timed_proc.is_alive():
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
        raise TimeoutError()
    else:
        try:
            res = q.get(block=False)
        except EmptyQueueError:
            # killed because of exceeding resources
            raise TimeoutError()
    return res


def problems_from_densities(input_files):
    """Returns a list of problems from the given list of input files.

    Args:
        input_files (list): list of input files in pywmi json format.

    Yields:
        A problem for each input file. A problem is a tuple filename, index, domain, support & query, weight.
    """
    input_files = sorted(
        [f for f in input_files if path.splitext(f)[1] == ".json"],
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


def get_random_sum(n, m):
    """Return a list of n numbers summing to m."""
    res = [0] * n
    for pos in random.choices(range(n), k=m):
        res[pos] += 1
    return res
