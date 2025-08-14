import argparse
from time import time
from typing import Callable

from pysmt.fnode import FNode
import pysmt.shortcuts as smt

from wmipa.solvers import AllSMTSolver
from wmipa.cli.density import Density
from wmipa.cli.log import logger
from wmipa.core.weights import Weights
from wmipa.enumeration import AsyncWrapper, Enumerator, SAEnumerator, TotalEnumerator
from wmipa.integration import (
    AxisAlignedWrapper,
    CacheWrapper,
    Integrator,
    LattEIntegrator,
    ParallelWrapper,
    RejectionIntegrator,
)

BASE_ENUMERATORS: dict[
    str, Callable[[FNode, Weights, argparse.Namespace], Enumerator]
] = {
    "sae": lambda support, weights, args: SAEnumerator(support, weights),
    "total": lambda support, weights, args: TotalEnumerator(support, weights),
}
WRAPPER_ENUMERATORS: dict[
    str, Callable[[Enumerator, argparse.Namespace], Enumerator]
] = {
    "async": lambda enumerator, args: AsyncWrapper(enumerator, args.async_queue_size),
}


BASE_INTEGRATORS: dict[str, Callable[[argparse.Namespace], Integrator]] = {
    "latte": lambda args: LattEIntegrator(),
    "rejection": lambda args: RejectionIntegrator(args.n_samples, args.seed),
}
WRAPPER_INTEGRATORS: dict[
    str, Callable[[Integrator, argparse.Namespace], Integrator]
] = {
    "axisaligned": lambda integrator, args: AxisAlignedWrapper(integrator),
    "cache": lambda integrator, args: CacheWrapper(integrator),
    "parallel": lambda integrator, args: ParallelWrapper(integrator, args.n_processes),
}


def parse_enumerator(
    support: FNode,
    weights: Weights,
    args: argparse.Namespace,
) -> Enumerator:
    curr, _, rest = args.enumerator.partition("-")

    if len(curr) == 0:
        # defaults to exhaustive TTA enumeration
        return TotalEnumerator(support, weights)
    elif len(rest) == 0:
        if curr not in BASE_ENUMERATORS:
            raise argparse.ArgumentTypeError(
                f"Unknown enumerator: {curr}. See help for available options."
            )
        return BASE_ENUMERATORS[curr](support, weights, args)
    else:
        # wrapper around enumerators
        if curr not in WRAPPER_ENUMERATORS:
            raise argparse.ArgumentTypeError(
                f"Unknown enumerator wrapper: {curr}. See help for available options."
            )
        args.enumerator = rest
        return WRAPPER_ENUMERATORS[curr](parse_enumerator(support, weights, args), args)


def parse_integrator(args: argparse.Namespace) -> Integrator:
    curr, _, rest = args.integrator.partition("-")

    if len(curr) == 0:
        # defaults to rejection
        return RejectionIntegrator()
    elif len(rest) == 0:
        if curr not in BASE_INTEGRATORS:
            raise argparse.ArgumentTypeError(
                f"Unknown integrator: {curr}. See help for available options."
            )
        return BASE_INTEGRATORS[curr](args)
    else:
        # wrapper around integrator
        args.integrator = rest
        if curr not in WRAPPER_INTEGRATORS:
            raise argparse.ArgumentTypeError(
                f"Unknown integrator wrapper: {curr}. See help for available options."
            )
        return WRAPPER_INTEGRATORS[curr](parse_integrator(args), args)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("filename", type=str, help="Path to the input density file")
    parser.add_argument(
        "--enumerator",
        type=str,
        default="total",
        help="Enumerator ({}, or wrapper: {}, possibly composed)".format(
            ", ".join(BASE_ENUMERATORS.keys()),
            ", ".join(f"{w}-..." for w in WRAPPER_ENUMERATORS.keys()),
        ),
    )
    parser.add_argument(
        "--async_queue_size",
        type=int,
        help="Size of the async queue (for async enumerators)",
    )
    parser.add_argument(
        "--integrator",
        type=str,
        default="rejection",
        help="Integrator ({}, or wrapper: {}, possibly composed)".format(
            ", ".join(BASE_INTEGRATORS.keys()),
            ", ".join(f"{w}-..." for w in WRAPPER_INTEGRATORS.keys()),
        ),
    )
    parser.add_argument(
        "--n_processes", type=int, help="Number of processes (for parallel integrators)"
    )
    parser.add_argument(
        "--n_samples", type=int, help="Number of samples (for MC-based integrators)"
    )
    parser.add_argument("--seed", type=int, help="seed (for randomized integrators)")


def run(args: argparse.Namespace) -> None:
    density = Density.from_file(args.filename)
    variables = [v for v in density.domain if v.symbol_type() == smt.REAL]

    enumerator = parse_enumerator(density.support, density.weights, args)
    integrator = parse_integrator(args)

    t0 = time()
    solver = AllSMTSolver(enumerator, integrator=integrator)

    result = solver.compute(smt.Bool(True), variables)
    tZ = time() - t0
    logger.info(f"Z: {result['wmi']}")
    logger.info(f"npolys: {result['npolys']}")
    logger.info(f"timeZ: {tZ}")

    for i, query in enumerate(density.queries):
        ti0 = time()
        result = solver.compute(query, variables)
        tif = time() - ti0
        logger.info(f"query{i}: {result['wmi']}")
        logger.info(f"npolys{i}: {result['npolys']}")
        logger.info(f"time{i}: {tif}")

    tfinal = time() - t0
    logger.info(f"time: {tfinal}")
