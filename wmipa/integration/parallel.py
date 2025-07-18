import numpy as np

from multiprocessing import Pool


class ParallelWrapper:

    DEF_N_PROCESSES = 8

    def __init__(self, integrator, n_processes=None):
        self.integrator = integrator
        self.n_processes = n_processes or ParallelWrapper.DEF_N_PROCESSES

    def integrate(self, polytope, polynomial):
        # do not even bother multiprocessing
        return self.integrator.integrate(polytope, polynomial)

    def integrate_batch(self, convex_integrals):
        with Pool(self.n_processes) as p:
            return np.array(p.map(self._unpack, convex_integrals))

    def _unpack(self, args):
        return self.integrator.integrate(*args)
