from collections import namedtuple
from multiprocessing import Queue, Process
from queue import Empty as EmptyQueueError

import psutil
from pysmt.shortcuts import Real, Bool
from pywmi import PyXaddEngine, XsddEngine, PyXaddAlgebra, FactorizedXsddEngine as FXSDD, RejectionEngine
from pywmi.engines.algebraic_backend import SympyAlgebra
from pywmi.engines.xsdd.vtrees.vtree import balanced

from wmipa import WMI
from wmipa.integration import LatteIntegrator, VolestiIntegrator, SymbolicIntegrator

WMIResult = namedtuple("WMIResult", ["wmi_id",
                                     "value",
                                     "n_integrations",
                                     "parallel_integration_time",
                                     "sequential_integration_time"])


def get_wmi_id(mode, integrator):
    """Return a string identifying the pair <mode, integrator>."""
    integrator_str = "" if integrator is None else f"_{integrator.to_short_str()}"
    return f"{mode}{integrator_str}"


def get_integrators(args):
    """Returns the integrators to be used for the given command line arguments."""
    if "PA" not in args.mode:
        return [None]
    if args.integrator == "latte":
        return [LatteIntegrator(n_threads=args.n_threads, stub_integrate=args.stub)]
    elif args.integrator == "volesti":
        seeds = list(range(args.seed, args.seed + args.n_seeds))
        return [VolestiIntegrator(n_threads=args.n_threads, stub_integrate=args.stub,
                                  algorithm=args.algorithm, error=args.error, walk_type=args.walk_type,
                                  walk_length=args.walk_length, seed=seed, N=args.N) for seed in seeds]
    elif args.integrator == "symbolic":
        return [SymbolicIntegrator(n_threads=args.n_threads, stub_integrate=args.stub)]
    else:
        raise ValueError(f"Invalid integrator {args.integrator}")


def compute_wmi(args, domain, support, weight):
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

    return res


def run_fn_with_timeout(fn, timeout, *args, **kwargs):
    """Run compute_wmi with a timeout. If the computation exceeds the timeout, a TimeoutError is raised."""
    q = Queue()

    def _wrapper(*args, **kwargs):
        _res = fn(*args, **kwargs)
        q.put(_res)

    timed_proc = Process(target=_wrapper, args=args, kwargs=kwargs)
    timed_proc.start()
    timed_proc.join(timeout)
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
