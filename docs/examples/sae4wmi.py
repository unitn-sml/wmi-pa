from pysmt.shortcuts import *

from wmpy.solvers import WMISolver

from wmpy.enumeration import SAEnumerator
from wmpy.integration import CacheWrapper, LattEIntegrator, ParallelWrapper


def instantiate_sae4wmi(support, w, smt_env, n_processes):
    enumerator = SAEnumerator(support, w, smt_env)
    integrator = CacheWrapper(
        ParallelWrapper(LattEIntegrator(), n_processes=n_processes)
    )
    return WMISolver(enumerator, integrator)
