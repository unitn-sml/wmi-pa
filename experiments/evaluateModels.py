import argparse
import os
import time
from os import path

from utils import check_input_output, compute_wmi_with_timeout, initialize_output_files, problems_from_densities, \
    write_result, WMIResult
from wmipa import WMI
from wmipa.integration.cache_integrator import CacheIntegrator
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
    parser.add_argument("-f", "--filename", help="Suffix for the result file (optional)")
    parser.add_argument("--timeout", type=int, default=3600, help="Max time (in seconds)")
    parser.add_argument("-m", "--mode", choices=modes, required=True, help="Mode to use")
    parser.add_argument("--n-threads", default=CacheIntegrator.DEF_N_THREADS, type=int,
                        help="Number of threads to use for WMIPA")
    parser.add_argument("-c", "--cache", type=int, choices=[-1, 0, 1, 2, 3], default=-1, help="Cache level for WMIPA methods")
    parser.add_argument("-t", "--stub", action="store_true",
                        help="Set this flag if you only want to count the number of integrals to be computed")
    parser.add_argument("--unweighted", action="store_true",
                        help="Set this flag if you want to compute the (unweighted) model integration, i.e., to use 1 as weight")

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

    check_input_output(args.input, args.output, args.filename)

    input_dir = os.path.split(args.input.rstrip("/"))[1]
    run_id = int(time.time())

    files = [fullpath for f in os.listdir(args.input) if path.isfile(fullpath := path.join(args.input, f))]

    output_files = initialize_output_files(args, input_dir, run_id)

    print(f"Started computing. RunID: {run_id}, args:\n{args}")
    print("Output files:\n\t{}".format("\n\t".join(output_files.values())))
    time_start = time.time()

    for i, (filename, query_n, domain, support, weight) in enumerate(problems_from_densities(files)):
        try:
            time_init = time.time()
            results = compute_wmi_with_timeout(args, domain, support, weight)
            time_total = time.time() - time_init
        except TimeoutError:
            results = [WMIResult(wmi_id=wmi_id, value=None, n_integrations=None, parallel_integration_time=0,
                                 sequential_integration_time=0) for wmi_id in output_files.keys()]
            time_total = args.timeout

        enumeration_time = time_total - sum(result.parallel_integration_time for result in results)

        for result in results:
            result: WMIResult

            effective_sequential_time = enumeration_time + result.sequential_integration_time
            effective_parallel_time = enumeration_time + result.parallel_integration_time

            result_json = {
                "filename": filename,
                "query": query_n,
                "value": result.value,
                "n_integrations": result.n_integrations,
                "sequential_integration_time": result.sequential_integration_time,
                "parallel_integration_time": result.parallel_integration_time,
                "sequential_time": effective_sequential_time,
                "parallel_time": effective_parallel_time,
            }

            output_file = output_files[result.wmi_id]
            write_result(output_file, result_json)

    print()
    print("Computed {} WMI".format(i + 1))

    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))


if __name__ == "__main__":
    main()
