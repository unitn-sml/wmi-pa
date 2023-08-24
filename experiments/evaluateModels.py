import argparse
import os
import time
from multiprocessing import Process, Queue
from os import path
from queue import Empty as EmptyQueueError

import psutil

from utils import compute_wmi, check_input_output, problems_from_densities, write_result
from wmipa import WMI
from wmipa.integration.volesti_integrator import VolestiIntegrator


def parse_args():
    modes = WMI.MODES + ["XADD", "XSDD", "FXSDD", "Rejection"]

    parser = argparse.ArgumentParser(
        description="Compute WMI on models",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", help="Folder with .json files")
    # parser.add_argument('-i', '--input-type', required=True,
    #                     help='Input type', choices=input_types.keys())
    parser.add_argument("-o", "--output", default=os.getcwd(),
                        help="Output folder where to save the result (default: cwd)")
    parser.add_argument("-f", "--filename", help="Name of the result file (optional)")

    parser.add_argument("--timeout", type=int, default=3600, help="Max time (in seconds)")

    parser.add_argument("-m", "--mode", choices=modes, required=True, help="Mode to use")
    parser.add_argument("--threads", default=None, type=int, help="Number of threads to use for WMIPA")

    parser.add_argument("-c", "--cache", choices=[-1, 0, 1, 2, 3], default=-1, help="Cache level for WMIPA methods")
    parser.add_argument("-t", "--stub", action="store_true",
                        help="Set this flag if you only want to count the number of integrals to be computed")

    integration_parsers = parser.add_subparsers(title="integration", description="Type of integration to use",
                                                dest="integration")
    latte_parser = integration_parsers.add_parser("latte", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    symbolic_parser = integration_parsers.add_parser("symbolic", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    volesti_parser = integration_parsers.add_parser("volesti", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    volesti_parser.add_argument("-e", "--error", default=0.1, type=float, help="Relative error acceptable [in (0, 1)]")
    volesti_parser.add_argument("--algorithm", choices=VolestiIntegrator.ALGORITHMS,
                                default=VolestiIntegrator.DEF_ALGORITHM,
                                help=f"Volume computation method: {', '.join(VolestiIntegrator.ALGORITHMS)}")
    volesti_parser.add_argument("--walk_type", choices=VolestiIntegrator.RANDOM_WALKS,
                                default=VolestiIntegrator.DEF_RANDOM_WALK,
                                help="Type of random walk: {', '.join(VolestiIntegrator.RANDOM_WALKS)}")
    volesti_parser.add_argument("-N", type=int, default=VolestiIntegrator.DEF_N, help="Number of samples")
    volesti_parser.add_argument("--walk_length", type=int, default=VolestiIntegrator.DEF_WALK_LENGTH,
                                help="Length of random walk (0 for default value)")
    volesti_parser.add_argument("--seed", type=int, default=666, help="Seed for random number generator")
    volesti_parser.add_argument("--n-seeds", type=int, default=1,
                                help="Number of seeds to use. The seed is incremented by 1 for each seed")

    return parser.parse_args()


def main():
    args = parse_args()
    # input_type = args.input_type
    output_file = args.filename
    long_mode = get_long_mode_name(args)

    check_input_output(args.input, args.output, args.filename)
    output_file = output_file or "{}_{}_{}.json".format(os.path.split(args.input.rstrip("/"))[1], long_mode,
                                                        int(time.time()))
    output_file = path.join(args.output, output_file)
    print("Creating... {}".format(output_file))

    files = [fullpath for f in os.listdir(args.input) if path.isfile(fullpath := path.join(args.input, f))]

    print("Started computing, mode: ", long_mode)
    time_start = time.time()

    for i, (filename, query_n, domain, support, weight) in enumerate(problems_from_densities(files)):
        try:
            time_init = time.time()
            res = compute_wmi_with_timeout(args, domain, support, weight)
            time_total = time.time() - time_init
        except TimeoutError:
            if args.integration == "volesti" and args.n_seeds > 1:
                raise NotImplementedError("Execution timed out while computing WMI using multiple integrators.")
            res = [(None, None, None, args.timeout, args.timeout)]
            time_total = args.timeout

        enumeration_time = time_total - sum(parallel_integration_time for *_, parallel_integration_time in res)

        for (seed, value, n_integrations, sequential_integration_time, parallel_integration_time) in res:
            effective_sequential_time = enumeration_time + sequential_integration_time
            effective_parallel_time = enumeration_time + parallel_integration_time

            res = {
                "filename": filename,
                "query": query_n,
                "seed": seed,
                "value": value,
                "n_integrations": n_integrations,
                "sequential_integration_time": sequential_integration_time,
                "parallel_integration_time": parallel_integration_time,
                "sequential_time": effective_sequential_time,
                "parallel_time": effective_parallel_time,
            }
            write_result(long_mode, res, output_file)

    print()
    print("Computed {} WMI".format(i + 1))

    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))


def compute_wmi_with_timeout(args, domain, support, weight):
    q = Queue()
    timed_proc = Process(
        target=compute_wmi,
        args=(domain, support, weight, args, q),
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


def get_long_mode_name(args):
    long_mode = args.mode
    if "PA" in args.mode:
        long_mode += "_" + args.integration
        if args.cache > -1:
            long_mode += "_cache_" + str(args.cache)
    return long_mode


if __name__ == "__main__":
    main()
