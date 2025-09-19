from multiprocessing import Pool
from typing import TYPE_CHECKING, Collection

import numpy as np

from wmpy.core import Polytope, Polynomial

if TYPE_CHECKING:  # avoid circular import
    from wmpy.integration import Integrator


class ParallelWrapper:
    """This class implements a multiprocessing integration wrapper."""

    DEF_N_PROCESSES = 8

    def __init__(self, integrator: "Integrator", n_processes: int = DEF_N_PROCESSES):
        """Default constructor.

        Attributes:
            integrator: the enclosed integrator instance
            n_processes: maximum number of spawnable subprocesses
        """
        self.integrator = integrator
        self.n_processes = n_processes

    def integrate(self, polytope: Polytope, polynomial: Polynomial) -> float:
        """Computes a convex integral.

        In principle, this should not be called.

        Args:
            polytope: convex integration bounds (a Polytope)
            polynomial: integrand (a Polynomial)

        Returns:
            The result of the integration as a non-negative scalar value.
        """

        # do not even bother multiprocessing
        return self.integrator.integrate(polytope, polynomial)

    def integrate_batch(
        self, convex_integrals: Collection[tuple[Polytope, Polynomial]]
    ) -> np.ndarray:
        """Computes a batch of integrals.

        Args:
            convex_integrals: a collection of bounds/integrand pairs

        Returns:
            The result of the batch of integrations as a numpy array.
        """
        with Pool(self.n_processes) as p:
            return np.array(p.map(self._unpack, convex_integrals))

    def _unpack(self, args: tuple[Polytope, Polynomial]) -> float:
        return self.integrator.integrate(*args)
