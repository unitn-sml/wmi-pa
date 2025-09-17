from pysmt.shortcuts import *

from wmipa.solvers import WMISolver

from wmipa.enumeration import SAEnumerator
from wmipa.integration import CacheWrapper, LattEIntegrator, ParallelWrapper


def instantiate_sae4wmi(support, w, smt_env, n_processes):
    enumerator = SAEnumerator(support, w, smt_env)
    integrator = CacheWrapper(
        ParallelWrapper(LattEIntegrator(), n_processes=n_processes)
    )
    return WMISolver(enumerator, integrator)
