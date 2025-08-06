from multiprocessing import Pool
from typing import TYPE_CHECKING, Collection

import numpy as np

from wmipa.datastructures import Polytope, Polynomial

if TYPE_CHECKING:  # avoid circular import
    from wmipa.integration import Integrator


class ParallelWrapper:

    DEF_N_PROCESSES = 8

    def __init__(self, integrator: "Integrator", n_processes: int = DEF_N_PROCESSES):
        self.integrator = integrator
        self.n_processes = n_processes

    def integrate(self, polytope: Polytope, polynomial: Polynomial) -> float:
        # do not even bother multiprocessing
        return self.integrator.integrate(polytope, polynomial)

    def integrate_batch(
        self, convex_integrals: Collection[tuple[Polytope, Polynomial]]
    ) -> np.ndarray:
        with Pool(self.n_processes) as p:
            return np.array(p.map(self._unpack, convex_integrals))

    def _unpack(self, args: tuple[Polytope, Polynomial]) -> float:
        return self.integrator.integrate(*args)
