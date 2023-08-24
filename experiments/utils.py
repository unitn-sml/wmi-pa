import json
import os
import sys
from os import path

from pysmt.shortcuts import Bool, reset_env, get_env
from pywmi import PyXaddEngine, XsddEngine, PyXaddAlgebra, FactorizedXsddEngine as FXSDD, RejectionEngine, Density
from pywmi.engines.algebraic_backend import SympyAlgebra
from pywmi.engines.xsdd.vtrees.vtree import balanced

from wmipa import WMI
from wmipa.integration import LatteIntegrator, VolestiIntegrator, SymbolicIntegrator


def compute_wmi(domain, support, weight, args, q):
    seeds = [0]
    if "PA" in args.mode:
        if args.integration == "latte":
            integrators = [LatteIntegrator()]
        elif args.integration == "volesti":
            seeds = list(range(args.seed, args.seed + args.n_seeds + 1))
            integrators = [VolestiIntegrator(algorithm=args.algorithm, error=args.error, walk_type=args.walk_type,
                                             walk_length=args.walk_length, seed=seed, N=args.N) for seed in seeds]
        elif args.integration == "symbolic":
            integrators = [SymbolicIntegrator()]
        else:
            raise ValueError(f"Invalid integrator {args.integrator}")

        wmi = WMI(support, weight, integrator=integrators)
        results, n_ints = wmi.computeWMI(
            Bool(True),
            mode=args.mode,
            cache=args.cache,
        )
        res = []
        for seed, result, n_int, integrator in zip(seeds, results, n_ints, integrators):
            res.append((seed, float(result), int(n_int), integrator.get_sequential_integration_time(),
                        integrator.get_parallel_integration_time()))
    else:
        if args.mode == "XADD":
            print(domain)
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

        res = [(None, wmi.compute_volume(add_bounds=False), 0, 0, 0)]

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
        # try:
        # reset pysmt environment
        reset_env()
        get_env().enable_infix_notation = True
        density = Density.from_file(filename)
        # except :
        #     print("Error on parsing", filename)
        #     # traceback.print_exception(type(ex), ex, ex.__traceback__)
        #     continue
        queries = density.queries or [Bool(True)]
        for j, query in enumerate(queries):
            print("\r" * 300, end="")
            print(
                "Problem: {} (query {}/{})/{} ({})".format(
                    i + 1, j + 1, len(queries), len(input_files), filename
                ),
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
