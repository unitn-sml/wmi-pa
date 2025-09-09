from typing import TYPE_CHECKING, Collection, Optional

import numpy as np

from wmipa.core import Polytope, Polynomial

if TYPE_CHECKING:  # avoid circular import
    from wmipa.integration import Integrator


class CacheWrapper:
    """This class implements a cache wrapper around an Integrator.

    The returned type of the integration calls is the same of the enclosed integrator.

    Attributes:
        integrator: the enclosed integrator instance
        cache: a dictionary mapping _compute_key(Polytope, Polynomial) into results
    """

    def __init__(self, integrator: "Integrator"):
        self.integrator = integrator
        self.cache: dict[int, float] = dict()

    def integrate(self, polytope: Polytope, polynomial: Polynomial) -> float:
        """Computes a convex integral.

        If the result is not yet available in the cache, the enclosed integrator is called (and the result is added to the cache).

        Args:
            polytope: convex integration bounds (a Polytope)
            polynomial: integrand (a Polynomial)

        Returns:
            The result of the integration as a non-negative scalar value.
        """
        key = CacheWrapper._compute_key(polytope, polynomial)
        if key not in self.cache:
            self.cache[key] = self.integrator.integrate(polytope, polynomial)

        return self.cache[key]

    def integrate_batch(
        self, convex_integrals: Collection[tuple[Polytope, Polynomial]]
    ) -> np.ndarray:
        """Computes a batch of integrals.

        Args:
            convex_integrals: a collection of bounds/integrand pairs

        Returns:
            The result of the batch of integrations as a numpy array.
        """
        volumes: list[Optional[float]] = [None] * len(convex_integrals)
        miss_indices, miss_batch, miss_keys = [], [], []
        for i, conv_int in enumerate(convex_integrals):
            key = CacheWrapper._compute_key(*conv_int)
            if key in self.cache:
                volumes[i] = self.cache[key]
            else:
                miss_indices.append(i)
                miss_batch.append(conv_int)
                miss_keys.append(key)

        for j, vol in enumerate(self.integrator.integrate_batch(miss_batch)):
            volumes[miss_indices[j]] = vol
            self.cache[miss_keys[j]] = vol

        return np.array(volumes)

    @staticmethod
    def _compute_key(polytope: Polytope, polynomial: Polynomial) -> int:
        """Computes an integer key given a pair of bounds and integrand.
        The current implementation is trivial, but it might be still worth using if multiple queries are computed on the same weighted SMT formula.
        """
        return hash(str(polytope) + str(polynomial))
